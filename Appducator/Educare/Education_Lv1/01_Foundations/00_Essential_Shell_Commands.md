# 00 - Essential Shell Commands for Vibe Coders
# 00 - Vibe 코더를 위한 필수 셸 명령어

The command line (or "shell") is a developer's most fundamental tool. Mastering a few essential commands will make you faster, more efficient, and more powerful. This is where the Vibe Coding journey begins.
명령줄(또는 "셸")은 개발자의 가장 기본적인 도구입니다. 몇 가지 필수 명령어를 마스터하면 더 빠르고 효율적이며 강력해질 것입니다. Vibe Coding 여정은 여기서 시작됩니다.

## Core Concepts
## 핵심 개념

1.  **Navigating**: Moving around your computer's file system.
    **탐색**: 컴퓨터 파일 시스템을 돌아다니는 것.
2.  **Inspecting**: Looking at files and directories.
    **검사**: 파일 및 디렉토리를 보는 것.
3.  **Manipulating**: Creating, editing, moving, and deleting files and directories.
    **조작**: 파일 및 디렉토리를 생성, 편집, 이동 및 삭제하는 것.
4.  **Piping and Redirecting**: Chaining commands together to perform complex tasks.
    **파이핑 및 리디렉션**: 복잡한 작업을 수행하기 위해 명령어를 연결하는 것.

---

## 1. Navigation: Your GPS
## 1. 탐색: 당신의 GPS

-   `pwd` (Print Working Directory): Shows you where you currently are.
    `pwd` (현재 작업 디렉토리 인쇄): 현재 위치를 보여줍니다.
    ```bash
    $ pwd
    /home/naru/work/2025-Public-Friend
    ```
-   `ls` (List): Lists the files and directories in the current location.
    `ls` (목록): 현재 위치의 파일 및 디렉토리 목록을 보여줍니다.
    -   `ls -l`: List in long format (shows permissions, owner, size, modification date).
        `ls -l`: 긴 형식으로 목록을 보여줍니다(권한, 소유자, 크기, 수정 날짜 표시).
    -   `ls -a`: List all files, including hidden ones (those starting with a `.`).
        `ls -a`: 숨겨진 파일(으)로 시작하는 파일 포함)을 포함한 모든 파일을 나열합니다.
    -   **Vibe Tip**: Use `ls -la` to get a detailed view of everything.
        **Vibe 팁**: `ls -la`를 사용하여 모든 것에 대한 자세한 보기를 얻으십시오.
-   `cd` (Change Directory): Moves you to another directory.
    `cd` (디렉토리 변경): 다른 디렉토리로 이동합니다.
    -   `cd druid_donum`: Move into a child directory.
        `cd druid_donum`: 하위 디렉토리로 이동합니다.
    -   `cd ..`: Move up to the parent directory.
        `cd ..`: 상위 디렉토리로 이동합니다.
    -   `cd ~` or just `cd`: Move to your home directory.
        `cd ~` 또는 그냥 `cd`: 홈 디렉토리로 이동합니다.
    -   `cd -`: Move to the previous directory you were in.
        `cd -`: 이전에 있던 디렉토리로 이동합니다.

---

## 2. Inspection: Your X-Ray Glasses
## 2. 검사: 당신의 X-레이 안경

-   `cat` (Concatenate): Prints the entire content of a file to the screen. Best for short files.
    `cat` (연결): 파일의 전체 내용을 화면에 인쇄합니다. 짧은 파일에 가장 적합합니다.
    ```bash
    $ cat README.md
    ```
-   `less`: Lets you view a file one page at a time. Best for long files.
    `less`: 한 번에 한 페이지씩 파일을 볼 수 있습니다. 긴 파일에 가장 적합합니다.
    -   Use arrow keys to navigate up and down.
        위아래로 이동하려면 화살표 키를 사용하십시오.
    -   Press `q` to quit.
        종료하려면 `q`를 누르십시오.
-   `head` / `tail`: Shows the first (`head`) or last (`tail`) 10 lines of a file.
    `head` / `tail`: 파일의 처음(`head`) 또는 마지막(`tail`) 10줄을 보여줍니다.
    -   `tail -n 20 log.txt`: Shows the last 20 lines.
        `tail -n 20 log.txt`: 마지막 20줄을 보여줍니다.
    -   **Vibe Tip**: `tail -f log.txt` ("follow") will continuously print new lines as they are added to the file. Essential for watching live logs.
        **Vibe 팁**: `tail -f log.txt`("따라가기")는 파일에 새 줄이 추가될 때마다 계속해서 인쇄합니다. 라이브 로그를 보는 데 필수적입니다.

---

## 3. Manipulation: Your Building Tools
## 3. 조작: 당신의 건축 도구

-   `touch`: Creates a new, empty file.
    `touch`: 새롭고 빈 파일을 만듭니다.
    ```bash
    $ touch new_file.txt
    ```
-   `mkdir` (Make Directory): Creates a new directory.
    `mkdir` (디렉토리 만들기): 새 디렉토리를 만듭니다.
    -   `mkdir -p path/to/nested/dir`: The `-p` flag creates all parent directories if they don't exist.
        `mkdir -p path/to/nested/dir`: `-p` 플래그는 존재하지 않는 경우 모든 상위 디렉토리를 만듭니다.
-   `cp` (Copy): Copies a file or directory.
    `cp` (복사): 파일 또는 디렉토리를 복사합니다.
    -   `cp source.txt destination.txt`: Copy and rename a file.
        `cp source.txt destination.txt`: 파일을 복사하고 이름을 바꿉니다.
    -   `cp -r source_dir/ destination_dir/`: The `-r` flag means "recursive" and is needed to copy a directory and its contents.
        `cp -r source_dir/ destination_dir/`: `-r` 플래그는 "재귀적"을 의미하며 디렉토리와 그 내용을 복사하는 데 필요합니다.
-   `mv` (Move): Moves or renames a file or directory.
    `mv` (이동): 파일 또는 디렉토리를 이동하거나 이름을 바꿉니다.
    -   `mv old_name.txt new_name.txt`: Renames a file.
        `mv old_name.txt new_name.txt`: 파일 이름을 바꿉니다.
    -   `mv file.txt path/to/dir/`: Moves a file into a directory.
        `mv file.txt path/to/dir/`: 파일을 디렉토리로 이동합니다.
-   `rm` (Remove): Deletes a file.
    `rm` (제거): 파일을 삭제합니다.
    -   `rm -i file.txt`: The `-i` flag prompts for confirmation before deleting.
        `rm -i file.txt`: `-i` 플래그는 삭제하기 전에 확인을 요청합니다.
    -   `rm -r directory/`: Deletes a directory and all its contents.
        `rm -r directory/`: 디렉토리와 그 안의 모든 내용을 삭제합니다.
    -   **⚠️ DANGER ZONE**: `rm -rf /` is a legendary command that will delete everything on your computer. The `-f` flag means "force" and will not ask for confirmation. **Use `rm -r` with extreme care.**
        **⚠️ 위험 지대**: `rm -rf /`는 컴퓨터의 모든 것을 삭제하는 전설적인 명령어입니다. `-f` 플래그는 "강제"를 의미하며 확인을 요청하지 않습니다. **`rm -r`은 극도의 주의를 기울여 사용하십시오.**

---

## 4. Piping and Redirection: The Superpower
## 4. 파이핑 및 리디렉션: 초능력

-   **`|` (Pipe)**: Takes the output of one command and uses it as the input for another. This lets you chain commands together.
    **`|` (파이프)**: 한 명령어의 출력을 가져와 다른 명령어의 입력으로 사용합니다. 이를 통해 명령어를 함께 연결할 수 있습니다.
    ```bash
    # Find all python files in the current directory and its subdirectories,
    # then count how many there are.
    # 현재 디렉토리와 그 하위 디렉토리에서 모든 파이썬 파일을 찾은 다음,
    # 몇 개가 있는지 셉니다.
    $ find . -name "*.py" | wc -l
    ```
-   **`>` (Redirect)**: Takes the output of a command and writes it to a file, overwriting the file if it exists.
    **`>` (리디렉션)**: 명령어의 출력을 가져와 파일에 씁니다. 파일이 존재하면 덮어씁니다.
    ```bash
    # List all files and save that list to a file named file_list.txt
    # 모든 파일을 나열하고 그 목록을 file_list.txt라는 파일에 저장합니다.
    $ ls -l > file_list.txt
    ```
-   **`>>` (Append Redirect)**: Takes the output of a command and adds it to the end of a file.
    **`>>` (추가 리디렉션)**: 명령어의 출력을 가져와 파일 끝에 추가합니다.
    ```bash
    # Add a separator and the current date to our log file
    # 로그 파일에 구분 기호와 현재 날짜를 추가합니다.
    $ echo "--- Log updated on $(date) ---" >> app.log
    ```

Mastering these commands will give you a solid foundation for navigating and controlling your development environment. Practice them until they become second nature.
이러한 명령어를 마스터하면 개발 환경을 탐색하고 제어하기 위한 견고한 기반을 갖게 될 것입니다. 제2의 천성이 될 때까지 연습하십시오.