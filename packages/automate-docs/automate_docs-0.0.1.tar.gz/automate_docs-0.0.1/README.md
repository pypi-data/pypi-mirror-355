# WriteReadMe

## Project Description
WriteReadMe is a tool designed to automate the process of generating comprehensive README.md files for any given GitHub repository. It uses Liberty GPT to analyze project structure and file contents, offering users a detailed and informative README.

## Key Features
- **Automated Cloning:** Safely clones any specified GitHub repository to a local directory for analysis.
- **Project Structure Analysis:** Generates a detailed tree of the project structure, allowing users to understand the layout of the repository.
- **Content Extraction:** Reads and extracts contents from relevant files to gather key information for README generation.
- **AI-Powered Documentation:** Utilizes AI to create professional README content tailored to the specific project.
- **Backup & Update:** Automatically backs up existing README files before updating them with the new version.
- **User-Friendly Interface:** Offers command line options for ease of use and customization.

## Technology Stack
- **Python:** Core language used for project development.
- **Git:** Essential for repository cloning and manipulation.
- **Liberty GPT AI:** Utilized for generating README content.


## Installation Instructions

To set up and use the WriteReadMe tool, follow these steps:



1. **Obtain Liberty GPT API Access Key:**

 Go to the [CORTEX webpage](https://cortex-lab.lmig.com/me) and log in.<br>
 Navigate to your profile and on the left hand side, click on the USER ACCESS TOKENS.<br>
 COPY your **User Token**<br>
  CREATE A .env file and paste it in the .env file under the name of "ACCESS_KEY="


2. **Clone the Repository:**
   ```bash
   git clone https://github.com/Natalio-Gomes_lmig/WriteReadMe.git
   cd WriteReadMe
   ```
3. **EXECUTE THE .SH FILES BASED ON YOUR OPERATING SYSTEM:**

For Windows users:  
Make sure you have Git Bash installed. You can download it from here: [https://git-scm.com/downloads]

```bash
chmod +x windows_setup.sh
./windows_setup.sh
```
For mac users:
```bash
chmod +x macOS_setup.sh
./macOS_setup.sh
```

4. **Run the Main Script:**
Execute the main script by providing the repository URL.
   ```bash
   python main.py [repository clone] 
   ```


## Usage Examples
Here's an example command to generate README for a repository:<br>
For Windows OS<br>

```bash
python main.py https://github.com/user/repository.git
```

<br>

For macOS<br>

```bash
python3 main.py https://github.com/user/repository.git
```

<br>
This command clones the specified repository, analyzes it, and generates a README.md within the cloned directory. 

### The cloned repository files will be under temp_repo_analysis\cloned_repo
Pay attention to the terminal

## Project Structure Overview

The WriteReadMe project structure is as follows:

```
automate-docs/
├── Requests
│   └── request.py
├── temp_repo_analysis
│   ├── cloned_repo
│   ├── file_contents.txt
│   └── project_tree.txt
├── .gitignore
├── git_push.sh
├── main.py
├── README.md
└── README.md.backup
```

- **Requests:** Houses external API call logic.
- **temp_repo_analysis:** Contains analysis outputs and the cloned project.
- **git_push.sh:** Script for streamlined Git operations (e.g., adding, committing, pushing changes).
- **main.py:** Entry point script for initializing the process of README generation.
- **README.md:** Contains project documentation.


## Configuration Details

- **AI API Keys:** Secure API keys via environment variables or configuration files.
- **File Inclusion/Exclusion:** Modify file extensions and directories to be included/excluded within `main.py`.

## Contributing Guidelines
Contributions to WriteReadMe are welcome! Please follow the guidelines below:

1. Fork the repository and create your branch from `main`.
2. Make your changes, ensuring comprehensive testing.
3. Submit a pull request for review.

## License Information
This project does not currently specify a license. Please ensure you adhere to any applicable legal and usage restrictions when using or contributing to this tool.

