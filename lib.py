#!/bin/python3
import subprocess
import os
import shutil
import pathlib


class Command:
    def execute(command, use_os=False):
        '''Execute bash command

        Arguments:
            command {str} -- full command

        Keyword Arguments:
            os {bool} -- should the os module be used instead of subprocess (default: {False})

        Returns:
            int/bool -- returncode/True if os is used
        '''
        if not use_os:
            command = command.split(' ')
            return subprocess.call(command)
        else:
            os.system(command)
            return True

    def get_output(command):
        '''Get standard output of command

        Arguments:
            command {str} -- full command

        Returns:
            str -- stdout
        '''
        command = command.split(' ')
        return subprocess.run(
            command, stderr=subprocess.STDOUT, stdout=subprocess.PIPE).stdout.decode('utf-8')

    def get_return_code(command):
        '''Get return code of command

        Arguments:
            command {str} -- full command

        Returns:
            int -- returncode
        '''
        command = command.split(' ')
        return subprocess.run(
            command, stderr=subprocess.STDOUT, stdout=subprocess.PIPE).returncode


class Color:
    '''Contains list of colors for printing'''
    def get_256_color(color):
        '''Get color using tput (256-colors base)

        Arguments:
            color {str/int} -- color id

        Returns:
            color -- color prefix for strings
        '''
        return Command.get_output(f'tput setaf {color}')

    def get_special_color(index):
        '''Get special colors using tput (like bold, etc..)

        Arguments:
            index {str} -- arguments following `tput` command

        Returns:
            color -- color prefix for strings
        '''
        return Command.get_output(f'tput {index}')

    RED = get_256_color(196)
    BLUE = get_256_color(51)
    GREEN = get_256_color(46)
    YELLOW = get_256_color(226)
    GOLD = get_256_color(214)
    GREY = get_256_color(238)

    RESET = get_special_color('sgr0')
    BOLD = get_special_color('bold')


class Print:
    def question(question):
        '''Print syntax for question

        Arguments:
            question {str} -- text to print (question)
        '''
        print(f'{Color.GREEN} // {question}{Color.RESET}')

    def question_options(options):
        '''Print syntax for options for question

        Arguments:
            options {str} -- options to print
        '''
        print(f'{Color.GREEN}    # {options}{Color.RESET}')

    def action(action):
        '''Print syntax for actions

        Arguments:
            action {str} -- text to print
        '''
        print(f'{Color.GOLD} >> {action}{Color.RESET}')

    def err(text):
        '''Print syntax for error

        Arguments:
            text {str} -- error text to print
        '''
        print(f'{Color.RED}   !! {text}{Color.RESET}')

    def cancel(text):
        '''Print syntax for cancellation

        Arguments:
            text {str} -- text to print
        '''
        print(f'{Color.GREY} >> {text}{Color.RESET}')

    def comment(text):
        '''Print syntax for comments

        Arguments:
            text {str} -- text to print
        '''
        print(f'{Color.GREY} // {text}{Color.RESET}')

    def warning(text):
        '''Print syntax for warnings

        Arguments:
            text {str} -- warn text to print
        '''
        print(f'{Color.YELLOW} ** {text}{Color.RESET}')


class Input:
    def yes_no(question):
        '''Generate question and wait for yes/no answer from user

        Arguments:
            question {str} -- question text

        Returns:
            bool -- question result (yes==true)
        '''
        Print.question(question)
        while True:
            ans = input('   Y/N: ')
            if ans.lower() == 'y' or ans == '':
                return True
            elif ans.lower() == 'n':
                return False
            else:
                Print.err('Invalid option (Y/N)')

    def multiple(question, options):
        '''Generate question and wait for user to pick one of options specified

        Arguments:
            question {str} -- question text
            options {list} -- list of possible options (strings)

        Returns:
            str -- one of options
        '''
        def get_input_range(max):
            while True:
                inp = input(' ->')
                try:
                    inp = int(inp)
                    for n in range(0, max + 1):
                        if inp == n:
                            return inp
                            break
                    else:
                        Print.err(f'Invalid input, range: 0-{max}')
                except ValueError:
                    Print.err(f'Invalid input (must be number: 0-{max})')
                    continue

        Print.question(question)

        Print.question_options('0: No/Cancel')
        for index, option in enumerate(options):
            Print.question_options(f'{index + 1}: {option}')

        answer = get_input_range(len(options))
        if answer != 0:
            return options[answer - 1]
        else:
            return False

    def question(text):
        Print.question(text)
        return input('   >>')

class Install:

    def _generate_install_text(install_text, package_name, yay=False, git=False):
        if install_text == 'default':
            install_text = f'Do you wish to install {package_name}?'
        if install_text[:10] == 'default + ':
            install_text = f'Do you wish to install {package_name}? {install_text[10:]}'
        if yay:
            install_text += '[AUR (YAY) Package]'
        if git:
            install_text += '[AUR (GIT+MAKEPKG) Package]'
        return install_text

    def check_installed(package_name):
        '''Check if specified package is currently installed

        Arguments:
            package_name {str} -- name of package/es to check

        Returns:
            bool -- is/are package/ss not installed?
        '''
        if type(package_name) == list:
            package_name = ' '.join(package_name)
        if type(package_name) == str:
            out = Command.get_return_code(f'pacman -Qi {package_name}')
            if out != 1:
                # INSTALLED
                return True
            else:
                # NOT INSTALLED
                return False
        else:
            raise TypeError(
                'check_installed() only takes string or list parameters')

    def check_not_installed(package_name):
        if type(package_name) == str:
            package_name = package_name.split(' ')
        elif type(package_name) != list:
            Print.err(
                'Function Install.check_not_installed() only accepts string or list parameters')
            raise TypeError(
                'check_not_installed() only takes string or list parameters')
        if package_name == ['base-devel']:
            # Check dependencies for base-devel (group packages are not detected directly)
            return Install.check_not_installed(
                'guile libmpc autoconf automake binutils bison fakeroot file findutils flex gawk gcc gettext grep groff gzip libtool m4 make pacman patch pkgconf sed sudo texinfo which')
        for package in package_name:
            if Install.check_installed(package):
                return False
                break
        else:
            return True

    def git_aur(repository, install_text='default', force=False):
        '''Install package directly from AUR using only git and makepkg

        Arguments:
            repository {string} -- repository name

        Keyword Arguments:
            install_text {str} -- text presented to the user before installing (default: {'default' -> 'Do you wish to install [repository]'})
            force {bool} -- should the repository be installed even if detected as installed (default: {False})

        Returns:
            bool -- installed
        '''

        if Install.check_not_installed('git'):
            Print.warning(
                f'Unable to install AUR repository: {repository}, git is not installed')
            return False

        # Base-devel group includes (required for makepkg)
        if Install.check_not_installed('base-devel'):
            Print.warning(
                f'Unable to install AUR repository: {repository}, base-devel is not installed')
            return False

        if Install.check_not_installed(repository) or force:
            install_text = Install._generate_install_text(
                install_text, repository, git=True)
            if Input.yes_no(install_text):
                url = f'https://aur.archlinux.org/{repository}.git'
                Command.execute(f'git clone {url}')
                os.chdir(repository)
                Command.execute('makepkg -si')
                os.chdir(Path.get_parent(__file__))
                shutil.rmtree(repository)
                return True
            else:
                Print.cancel('Skipping...')
                return False
        else:
            Print.cancel(
                f'assuming {repository} already installed ({repository} is installed)')
            return True

    def package(package_name, install_text='default', aur=False, reinstall=False):
        '''Installation of package

        Arguments:
            package_name {str} -- name of package to be installed

        Keyword Arguments:
            install_text {str} -- text presented to user before installing (default: {'default' -> 'Do you wish to install [package_name]'})
            use_yay {bool} -- use yay for package installation (default: {False})
            reinstall {bool} -- should the package be reinstalled (default {False})

        Returns:
            bool -- installed
        '''
        if aur:
            if Install.check_not_installed('yay'):
                Print.cancel(
                    f'Unable to install with yay (not installed), installing AUR package: {package_name} with git instead')
                Install.git_aur(package_name, install_text)
        if Install.check_not_installed(package_name) or reinstall:
            install_text = Install._generate_install_text(
                install_text, package_name, yay=aur)
            if Input.yes_no(install_text):
                if aur:
                    Command.execute(f'yay -S {package_name}')
                else:
                    Command.execute(f'sudo pacman -S {package_name}')
                return True
            else:
                Print.cancel('Skipping...')
                return False
        else:
            Print.cancel(f'{package_name} already installed')
            return True

    def multiple_packages(packages, install_text, options=False, reinstall=False):
        '''Installation of multiple packages

        Arguments:
            packages {list} -- list of packages to choose from
            install_text {str} -- text presented to user when picking which package to install
            options {list} -- list of options to choose from (must be in same order as packages)

        Returns:
            bool/str -- False if none / chosen package name
        '''
        if Install.check_not_installed(packages) or reinstall:
            if not options:
                options = packages
            choice = Input.multiple(f'{install_text}', options)
            if choice:
                for index, option in enumerate(options):
                    if choice == option:
                        Command.execute(f'sudo pacman -S {packages[index]}')
                        return packages[index]
            else:
                Print.cancel('Skipping...')
                return False
        else:
            for package in packages:
                if not Install.check_not_installed(package):
                    Print.cancel(f'{package} already installed')
            return False

    def upgrade_pacman():
        if Input.yes_no('Do you wish to Sync(S), refresh(y) and upgrade(u) pacman - Recommended?'):
            Command.execute('sudo pacman -Syu')
        else:
            Print.warning('Pacman upgrade cancelled.')


class Path:
    def check_dir_exists(paths):
        '''Check for directory/ies existence

        Arguments:
            paths {str} -- single path or multiple paths separated by spaces (absolute paths)

        Returns:
            bool -- One of dirs exists/Single dir exists
        '''
        if type(paths) != str:
            paths = str(paths)
        paths = paths.split(' ')
        for dir_path in paths:
            dir_path = os.path.expanduser(dir_path)
            if os.path.isdir(dir_path):
                return True
                break
        else:
            return False

    def check_file_exists(paths):
        '''Check for file/s existence

        Arguments:
            paths {str} -- single path or multiple paths separated by spaces (absolute paths)

        Returns:
            bool -- One of files exists/Single file exists
        '''
        if type(paths) != str:
            paths = str(paths)
        paths = paths.split(' ')
        for file_path in paths:
            file_path = os.path.expanduser(file_path)
            if os.path.isfile(file_path):
                return True
                break
        else:
            return False

    def get_parent(file_path):
        '''Get Parent directory of specified file

        Arguments:
            file {str} -- path to file

        Returns:
            str -- directory to file
        '''
        return pathlib.Path(file_path).parent.absolute()

    def get_all_files(dir_path):
        '''Get list of all files in specified directory (recursive)

        Arguments:
            dir_path {str/Path} -- path to starting directory

        Returns:
            list -- files found
        '''
        files_found = []
        for subdir, dirs, files in os.walk(dir_path):
            for file in files:
                files_found.append(os.path.join(subdir, file))
        return files_found

    def get_all_dirs_and_files(dir_path):
        '''Get list of all files and directories in specified directory (recursive)

        Arguments:
            dir_path {str/Path} -- path to starting directory

        Returns:
            list, list-- files, dirs found
        '''
        files_found = []
        dirs_found = []
        for subdir, dirs, files in os.walk(dir_path):
            for file in files:
                files_found.append(os.path.join(subdir, file))
            for directory in dirs:
                dirs_found.append(os.path.join(subdir, directory))
        return files_found, dirs_found

    def ensure_dirs(path, absolute_path=True):
        '''Ensure existence of directories (usually before creating files in it)

        Arguments:
            path {str} -- full path - will check every directory it contains

        Keyword Arguments:
            file_end {bool} -- does path end with file? (default: {False})
            absolute_path {bool} -- is path absolute? (default: {True})
        '''
        if not absolute_path:
            path = pathlib.Path(path).absolute()
        if Path.check_file_exists(path):
            path = Path.get_parent(path)

        if not Path.check_dir_exists(path):
            Command.execute(f'mkdir -p {path}')
            Print.comment(f'Creating directory {path}')

    def get_home():
        '''Get home path

        Returns:
            str -- path to user home
        '''
        return os.environ['HOME']

    def create_symlink(symlink_pointer, path):
        '''Create Symbolic link

        Arguments:
            symlink_pointer {str} -- path where symlink should be pointing
            path {str} -- path in which the symlink should be created
        '''
        Path.ensure_dirs(path)
        Command.execute(f'ln -sf {symlink_pointer} {path}')
        Print.comment(f'Created symlink: {path} -> {symlink_pointer}')

    def copy(path, copied_path):
        '''Create copy of specified file

        Arguments:
            path {str} -- path to original file
            copied_path {str} -- path to new file
        '''
        Path.ensure_dirs(copied_path)
        Command.execute(f'cp {path} {copied_path}')
        Print.comment(f'Copied {path} to {copied_path}')
