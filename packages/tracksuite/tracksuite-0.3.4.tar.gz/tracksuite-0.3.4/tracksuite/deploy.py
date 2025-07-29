import argparse
import os
import tempfile
from filecmp import dircmp

import git

from .utils import run_cmd


class GitDeployment:
    def __init__(
        self,
        host=None,
        user=None,
        staging_dir=None,
        local_repo=None,
        target_repo=None,
        backup_repo=None,
    ):
        """
        Class used to deploy suites through git.

        Parameters:
            host(str): The target host.
            user(str): The deploying user.
            staging_dir(str): The source suite directory.
            local_repo(str): Path to the local repository.
            target_repo(str): Path to the target repository on the target host.
            backup_repo(str): URL of the backup repository.
        """

        print("Creating deployer:")
        self.deploy_user = os.getenv("USER")
        self.deploy_host = os.getenv("HOSTNAME")
        self.user = self.deploy_user if user is None else user
        self.host = self.deploy_host if host is None else host

        self.staging_dir = staging_dir
        if self.staging_dir is None:
            raise Exception("Staging directory not specified")

        if local_repo is None:
            local_repo = tempfile.mkdtemp(prefix="suite_")
        self.local_dir = local_repo

        self.target_dir = target_repo

        # setup local repo
        # for test purpose with /tmp folders, stay local with localhost
        if self.host == "localhost":
            self.target_repo = f"{target_repo}"
        else:
            self.target_repo = f"ssh://{self.user}@{self.host}:{target_repo}"
        try:
            print(f"    -> Loading local repo {local_repo}")
            self.repo = git.Repo(local_repo)
        except (git.exc.NoSuchPathError, git.exc.InvalidGitRepositoryError):
            print(f"    -> Cloning from {self.target_repo}")
            self.repo = git.Repo.clone_from(self.target_repo, local_repo, depth=1)
            self.repo.remotes["origin"].rename("target")

        # get the name of the default branch
        self.default_branch = self.repo.active_branch.name

        # link with backup repo
        self.backup_repo = backup_repo
        if backup_repo and "backup" not in self.repo.remotes:
            print(f"    -> Creating backup remote {backup_repo}")
            self.repo.create_remote("backup", url=backup_repo)
            self.sync_remotes()

    def get_hash_remote(self, remote):
        """
        Get the git hash of a remote repository on the default branch.

        Parameters:
            remote(str): Name of the remote repository (typically "target").

        Returns:
            The git hash of the default branch.
        """
        remote_branch = self.repo.remotes[remote].refs[self.default_branch]
        return remote_branch.commit.hexsha

    def check_sync_local_remote(self, remote):
        """
        Check that the local repository git hash is the same as the remote.
        Raise exception if the git hashes don't match.

        Parameters:
            remote(str): Name of the remote repository (typically "target").

        Returns:
            The matching git hash.
        """
        remote_repo = self.repo.remotes[remote]
        remote_repo.fetch()
        hash_target = self.get_hash_remote(remote)
        hash_local = self.repo.active_branch.commit.hexsha
        if hash_target != hash_local:
            print(f"Local hash {hash_local}")
            print(f"Target hash {hash_target}")
            raise Exception(
                f"Local ({self.local_dir}) and remote ({remote}) git repositories not in sync!"
            )
        return hash_local

    def check_sync_remotes(self, remote1, remote2):
        """
        Check that two remote repositories have the same git hash.
        Raise exception if the git hashes don't match.

        Parameters:
            remote1(str): Name of the first remote repository (typically "target").
            remote2(str): Name of the second remote repository (typically "backup").

        Returns:
            The matching git hash.
        """
        remote_repo1 = self.repo.remotes[remote1]
        remote_repo2 = self.repo.remotes[remote2]
        remote_repo1.fetch()
        remote_repo2.fetch()
        hash1 = self.get_hash_remote(remote1)
        hash2 = self.get_hash_remote(remote2)
        if hash1 != hash2:
            print(f"Remote {remote1} hash {hash1}")
            print(f"Remote {remote2} hash {hash2}")
            raise Exception(
                f"Remote git repositories ({remote1} and {remote2}) not in sync!"
            )
        return hash1

    def commit(self, message=None, files=None):
        """
        Commits the current stage of the local repository.
        Throws exception if there is nothing to commit.
        Default commit message will be:
            "deployed by {user} from {host}:{staging_dir}"

        Parameters:
            message(str): optional git commit message to append to default message
        """
        if files is None:
            files = "--all"
        try:
            commit_message = f"deployed by {self.deploy_user} from {self.deploy_host}:{self.staging_dir}\n"
            if message:
                commit_message += message
            self.repo.git.add(files)
            diff = self.repo.index.diff(self.repo.commit())
            if diff:
                self.repo.index.commit(commit_message)
            else:
                return False
        except Exception as e:
            print("Commit failed!")
            raise e
        return True

    def push(self, remote):
        """
        Pushes the local state to the remote repository

        Parameters:
            remote(str): Name of the remote repository (typically "target").
        """
        remote_repo = self.repo.remotes[remote]
        try:
            remote_repo.push().raise_if_error()
        except git.exc.GitCommandError:
            raise git.exc.GitCommandError(
                f"Could not push changes to remote repository {remote}. "
                + "Check configuration and the state of the remote repository! "
                + "The remote repository might have uncommited changes."
            )

    def pull_remotes(self):
        """
        Git pull the remote repository to the local repository
        """
        remote_repo = self.repo.remotes["target"]
        remote_repo.pull()
        self.check_sync_local_remote("target")
        if self.backup_repo:
            self.sync_remotes()

    def diff_staging(self):
        """
        Prints the difference between the staged suite and the current suite
        """
        modified = []
        removed = []
        added = []

        def get_diff_files(dcmp, root=""):
            for name in dcmp.diff_files:
                path = os.path.join(root, name)
                modified.append(path)
            for name in dcmp.left_only:
                path = os.path.join(root, name)
                fullpath = os.path.join(self.staging_dir, path)
                if os.path.isdir(fullpath):
                    for root_dir, dirs, files in os.walk(fullpath):
                        for file in files:
                            filepath = os.path.relpath(
                                os.path.join(root, root_dir, file), self.staging_dir
                            )
                            added.append(filepath)
                else:
                    added.append(path)
            for name in dcmp.right_only:
                path = os.path.join(root, name)
                fullpath = os.path.join(self.target_dir, path)
                if os.path.isdir(fullpath):
                    for root_dir, dirs, files in os.walk(fullpath):
                        for file in files:
                            filepath = os.path.relpath(
                                os.path.join(root, root_dir, file), self.target_dir
                            )
                            removed.append(filepath)
                else:
                    removed.append(path)
            for dir, sub_dcmp in dcmp.subdirs.items():
                get_diff_files(sub_dcmp, root=os.path.join(root, dir))

        diff = dircmp(self.staging_dir, self.local_dir)
        print("Changes in staged suite:")
        get_diff_files(diff)
        changes = [
            ("Removed", removed),
            ("Added", added),
            ("Modified", modified),
        ]
        for name, files in changes:
            if files:
                print(f"    - {name}:")
                for path in files:
                    print(f"        - {path}")
        print("For more details, compare the following folders:")
        print(self.staging_dir)
        print(self.local_dir)

    def deploy(self, message=None, files=None):
        """
        Deploy the staged suite to the target repository.
        Steps:
            - git fetch remote repositories and check they are in sync
            - rsync the staged folder to the local repository
            - git add all the suite files and commit
            - git push to remotes
        Default commit message will be:
            "deployed by {user} from {host}:{staging_dir}"

        Parameters:
            message(str): optional git commit message to append to default message.
        """
        print("Deploying suite to remote locations")
        # check if repos are in sync
        print("    -> Checking that git repos are in sync")
        hash_init = self.check_sync_local_remote("target")
        if self.backup_repo:
            self.check_sync_local_remote("backup")
            self.check_sync_remotes("target", "backup")

        # rsync staging folder to current repo
        print("    -> Staging suite")

        rsync_options = "-avzc --delete  --exclude .git "
        cmd = f"rsync {rsync_options} {self.staging_dir}/ {self.local_dir}/"
        run_cmd(cmd)

        # git commit and push to remotes
        print("    -> Git commit")
        if not self.commit(message, files):
            print("Nothing to commit... aborting")
            return False
        print(f"    -> Git push to target {self.target_repo} on host {self.host}")

        hash_check = self.get_hash_remote("target")
        if hash_check != hash_init:
            raise Exception(
                "Remote repositories have changed during deployment!\n \
                Please check the state of the remote repositories"
            )

        self.push("target")
        if self.backup_repo:
            print(f"    -> Git push to backup repository {self.backup_repo}")
            self.push("backup")

        return True

    def sync_remotes(self):
        """
        Sync the remote repositories.
        Steps:
            - git fetch remote repositories and check they are in sync
            - git push to backup if needed
        """
        try:
            self.check_sync_local_remote("backup")
            self.check_sync_remotes("target", "backup")
        except Exception:
            print("WARNING! Backup repository outdated. Pushing update to backup")
            self.push("backup")


def main(args=None):
    description = "Suite deployment tool"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--stage", required=True, help="Staged suite")
    parser.add_argument(
        "--target", required=True, help="Path to target git repository on host"
    )
    parser.add_argument(
        "--local",
        help="Path to local git repository (will be created if doesn't exist)",
    )
    parser.add_argument("--backup", help="URL to backup git repository")
    parser.add_argument("--host", default=os.getenv("HOSTNAME"), help="Target host")
    parser.add_argument("--user", default=os.getenv("USER"), help="Deploy user")
    parser.add_argument("--message", help="Git message")
    parser.add_argument(
        "--push", action="store_true", help="Push staged suite to target"
    )
    parser.add_argument(
        "-f",
        "--files",
        nargs="+",
        help="Specific files to deploy, by default everything is deployed",
    )

    args = parser.parse_args()

    print("Initialisation options:")
    print(f"    - host: {args.host}")
    print(f"    - user: {args.user}")
    print(f"    - staged suite: {args.stage}")
    print(f"    - local repo: {args.local}")
    print(f"    - target repo: {args.target}")
    print(f"    - backup repo: {args.backup}")
    print(f"    - git message: {args.message}")
    print(f"    - files to deploy: {args.files}")

    deployer = GitDeployment(
        host=args.host,
        user=args.user,
        staging_dir=args.stage,
        local_repo=args.local,
        target_repo=args.target,
        backup_repo=args.backup,
    )

    deployer.pull_remotes()
    deployer.diff_staging()

    if args.push:
        if args.files is not None:
            print("Deploying only the following files:")
            for f in args.files:
                print(f"    - {f}")

        check = input(
            "You are about to push the staged suite to the target directory. Are you sure? (y/N)"
        )
        if check != "y":
            exit(1)
        deployer.deploy(args.message, args.files)


if __name__ == "__main__":
    main()
