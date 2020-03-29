from lib import Input, Print, Install, Path
import os
from datetime import datetime

def make_backup(files_dir):
    if Input.yes_no('Do you wish to create a backup of current state of your dotfiles?'):
        Print.action('Creating dotfiles backup')
        backup_dir = str(datetime.now()).replace(' ', '--')
        current_backup_dir = os.path.join(Path.get_parent(__file__), 'Backups', backup_dir)
        Path.ensure_dirs(current_backup_dir)
        for file in Path.get_all_files(files_dir):
            from_pos = os.path.join(
            Path.get_home(), file.replace(f'{files_dir}/', ''))
            to_pos = os.path.join(
            current_backup_dir, file.replace(f'{files_dir}/', ''))
            if Path.check_file_exists(from_pos):
                Path.copy(from_pos, to_pos)

        Print.action('Backup complete')
        return True
    else:
        Print.warning('Proceeding without backup')
        return False


def check_installation():
    if Install.check_not_installed('zsh'):
        if not Install.package('zsh', 'default + (This is required shell for dotfiles)'):
            Print.err('Dotfiles installation cancelled - zsh not installed')
            return False

    global oh_my_zsh_path, zsh_highlight_path

    zsh_highlight_path = None
    if Path.check_file_exists('/usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh'):
        zsh_highlight_path = '/usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh'

    oh_my_zsh_path = None
    if Path.check_dir_exists('~/.oh-my-zsh'):
        oh_my_zsh_path = '$HOME/.oh-my-zsh'
    elif Path.check_dir_exists('~/oh-my-zsh'):
        oh_my_zsh_path = '$HOME/oh-my-zsh'
    elif Path.check_dir_exists('~/ohmyzsh'):
        oh_my_zsh_path = '$HOME/ohmyzsh'
    elif Path.check_dir_exists('~/.config/oh-my-zsh'):
        oh_my_zsh_path = '$HOME/.config/oh-my-zsh'
    elif Path.check_dir_exists('/usr/share/oh-my-zsh'):
        oh_my_zsh_path = '/usr/share/oh-my-zsh'

    if oh_my_zsh_path:
        return True
    else:
        Print.err('oh-my-zsh is not installed, cannot proceed...')
        # TODO: Option to install
        return False



def personalized_changes(file):
    if '.zshrc' in file:
        global oh_my_zsh_path, zsh_highlight_path
        filedata = None
        with open(file, 'r') as f:
            filedata = f.read()
        filedata_old = filedata

        # Change path to oh-my-zsh
        filedata = filedata.replace('"$HOME/.config/oh-my-zsh"', f'"{oh_my_zsh_path}"')

        # Change path to zsh-color-highlight
        if zsh_highlight_path is not None:
            original_path='/usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh'
            filedata = filedata.replace(f'source {original_path}', f'source {zsh_highlight_path}')
        else:
            if Install.package('zsh-syntax-highlighting', 'default'):
                zsh_highlight_path = Input.question('Please specify path to your zsh-syntax-highlighting plugin (blank=do not include)')
                if zsh_highlight_path != '':
                    filedata = filedata.replace(f'source {original_path}', f'source {zsh_highlight_path}')
                else:
                    filedata = filedata.replace(f'source {original_path}', f'')
            else:
                filedata = filedata.replace(f'source {original_path}', f'')

        if filedata_old != filedata:
            Print.commend('Changing oh-my-zsh location in .zshrc')
            with open(file, 'w') as f:
                f.write(filedata)

    if 'vimrc' in file:
        if not Input.yes_no('Do you wish to use .vimrc (If you choose yes, please install Vundle or you will get errors)'):
            # TODO: Install vundle
            return False
    return True


def init(symlink):
    # Get path to files/ floder (contains all dotfiles)
    files_dir = os.path.join(
        Path.get_parent(__file__), 'files')
    # Create optional backup
    make_backup(files_dir)
    files_list, dirs_list = Path.get_all_dirs_and_files(files_dir)

    # Create all dirs
    for directory in dirs_list:
        position = os.path.join(
            Path.get_home(), directory.replace(f'{files_dir}/', ''))
        Path.ensure_dirs(position)

    # Go through all files
    for file in files_list:
        # Make personalized changes to files
        personalized_changes(file)
        # Set symlink position ($HOME/filepath)
        position = os.path.join(
            Path.get_home(), file.replace(f'{files_dir}/', ''))

        if symlink:
            # Make symlink
            Path.create_symlink(file, position)
        else:
            Path.copy(file, position)


def main():
    Print.action('Installing dotfiles')

    if not check_installation():
        return False

    choice = Input.multiple('Do you wish to create dotfiles', [
                            'symlinks (dotfiles/ dir will be required)', 'files (dotfiles/ dir can be removed afterwards)'])
    # Create symlinks
    if choice == 'symlinks (dotfiles/ dir will be required)':
        init(symlink=True)

        # Final prints
        Print.action('Symlink installation complete')
        Print.warning(
            'Do not delete this floder, all dotfile symlinks are linked to it')
        Print.warning(
            'Deletion would cause errors on all your dotfiles managed by this program')
        Print.comment(
            'If you wish to remove this floder, please select files instead of symlinks for dotfile creation')

    # Create files
    elif choice == 'files (dotfiles/ dir can be removed afterwards)':
        init(symlink=False)

        # Final prints
        Print.action('Dotfiles successfully created')
        Print.comment('This directory can now be removed')

    # Don't create dotfiles
    else:
        Print.cancel('Dotfiles installation cancelled')
        return False


if __name__ == "__main__":
    main()
