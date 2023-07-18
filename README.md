# CodeCommit

CodeCommit is a script that simplifies the process of generating a commit message for staged files and committing them using Git. It combines a Python script and a Bash script to activate the necessary environment and run the Python code.

## Requirements

- Git
- Conda (Anaconda or Miniconda)

## Setup

1. Clone the repository and navigate to the project directory.

2. Install the required dependencies by creating a Conda environment:

```bash
git clone git@github.com:kandapagari/CodeCommit.git
conda create --name codecommit python=3.10
conda activate codecommit
pip install poetry
poetry install
```

3. Either export `OPENAI_API_KEY` as an environment variable or add it to the `.env` file in the root of the repository. see [OpenAI API](https://platform.openai.com/docs/api-reference/authentication) for more information and .env.example for an example.

```bash
export OPENAI_API_KEY=<your-api-key>
```

4. Set up the alias by adding the following line to your shell configuration file (e.g., ~/.bashrc, ~/.zshrc):

```bash
alias codecommit='bash /path/to/CodeCommit/run.sh'
```

## Usage

```bash
codecommit
```

### Options

- No options: Run the Python script to generate and commit the changes.
- `-h, --help`: Display help information.

### Workflow

1. Stage your changes using `git add`.

2. Run the `codecommit` alias.

3. The script will activate the `codecommit` Conda environment and execute the Python script `app/codecommit.py`.

4. Git will prompt you to edit the generated commit message. Make any necessary modifications and save the file to complete the commit.

### Example

run this command in from the root of the repository:

```bash
codecommit
```

This will generate a commit message for the staged files and initiate the commit process. Git will open a text editor for you to review and modify the generated commit message.

## License

This project is licensed under the [MIT License](LICENSE).
