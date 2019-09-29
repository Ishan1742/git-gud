from argparse import ArgumentParser

from git import Repo
from git import Actor


def parse_tree(tree_str):
    # The purpose of this method is to get a more computer-readable commit tree

    commits = []  # List of  (commit_name, [parents], [branches], [tags])
    all_branches = set()
    all_tags = set()

    for line in tree_str.split('\n'):
        if line[0] == '#':
            continue
        line = line.replace('  ', '')

        if '(' in line:
            commit_str = line[:line.find('(')].strip()
            ref_str = line[line.find('(')+1:-1].strip().replace(' ', '')
        else:
            commit_str = line.strip()
            ref_str = ''

        if ':' not in commit_str:
            # Implicit parent, use previous commit
            if len(commits) == 0:
                parents = []
            else:
                parents = [commits[len(commits)-1][0]]
            commit_name = commit_str
        else:
            # Find parent
            commit_name, parent_str = commit_str.split(':')
            commit_name = commit_name.strip()
            parent_str = parent_str.strip()

            if parent_str:
                parents = parent_str.split(' ')
            else:
                parents = []

        # We know the commit name and parents now

        assert ' ' not in commit_name  # There should never be more than one change or a space in a name

        # Process references
        if ref_str:
            refs = ref_str.split(',')
        else:
            refs = []
        branches = []
        tags = []
        for ref in refs:
            if ref[:4] == 'tag:':
                tag = ref[4:]
                assert tag not in all_tags
                tags.append(tag)
                all_tags.add(tag)
            else:
                branch = ref
                assert branch not in all_branches
                branches.append(branch)
                all_branches.add(branch)
        commits.append((commit_name, parents, branches, tags))

    head = commits[-1][0]
    del commits[-1]

    return commits, head


def level_json(commits, head):
    # We've formally replicated the input string in memory

    level = {
        'topology': [],
        'branches': {},
        'tags': {},
        'commits': {},
        'HEAD': {},
    }

    all_branches = []
    all_tags = []
    for commit_name, parents, branches_here, tags_here in commits:
        level['topology'].append(commits)
        level['commits'][commit_name] = {
            'parents': parents,
            'id': commit_name
        }
        if not parents:
            level['commits'][commit_name]['rootCommit'] = True
        all_branches.extend(branches_here)
        all_tags.extend(tags_here)

        for branch in branches_here:
            level['branches'][branch] = {
                'target': commit_name,
                'id': branch
            }

        for tag in tags_here:
            level['tags'][tag] = {
                'target': commit_name,
                'id': tag
            }

    level['HEAD'] = {
        'target': head,
        'id': 'HEAD'
    }

    return level


def add_file_to_index(index, filename):
    # TODO Want to do this in the working directory
    # TODO Use tree only when in dev-mode
    open(f'tree/{filename}', 'w+').close()
    index.add([filename])


class Commit:
    def __init__(self, name):
        self.name = name
        self.children = []


def get_branching_tree(tree):
    # TODO Delete this function and Commit class
    commits = {}

    for commit in tree['commits']:
        for parent in commit['parents']:
            if parent not in commits:
                commits[parent] = Commit(parent)
            commits[parent].children.append(commit)

    return commits


def create_tree(commits, head):
    # tree['commits']
    # First, find the initial commit
    # Should I go depth first or breadth first?
    # TODO Clear tree
    repo = Repo('tree') # TODO Only use tree in dev-mode
    index = repo.index

    author = Actor("Git Gud", "git-gud@example.com")

    commits = {}

    for name, parents, branches, tags in commits:
        # commit = (name, parents, branches, tags)
        # TODO Test whether the branches are created properly
        # TODO Figure out how to handle merges
        add_file_to_index(index, name) # TODO Files don't need diffs, consider just committing
        parents = [commits[parent] for parent in parents]
        if parents:
            repo.active_branch.set_commit(parents[0])
        commit = index.commit(name, author=author, committer=author, head=True, parent_commits=parents)
        commits[name] = commit

        for branch in branches:
            repo.create_head(branch, commit)

        for tag in tags:
            repo.create_tag(tag, commit)

    for branch in repo.branches:
        if branch.name == head:
            branch.checkout()
    # TODO use single branch for all commits then delete branch at the end
    # TODO How do we change the commit of a branch


# TODO Commit
# TODO Test
# TODO Save
# TODO Load
# TODO Instructions
# TODO convert commit tree into spec format
# TODO convert spec format into commit tree

def main():
    with open('spec.spec') as spec_file:
        commits, head = parse_tree(spec_file.read())
        create_tree(commits, head)

    pass


if __name__ == '__main__':
    main()
