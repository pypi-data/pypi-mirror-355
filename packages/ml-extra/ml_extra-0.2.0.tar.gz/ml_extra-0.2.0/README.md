<p align="left">
    <h1 align="left">ML-EXTRA</h1>
</p>
<p align="left">
		<em>Developed with the software and tools below.</em>
</p>
<p align="left">
	<img src="https://img.shields.io/badge/YAML-CB171E.svg?style=flat-square&logo=YAML&logoColor=white" alt="YAML">
	<img src="https://img.shields.io/badge/Poetry-60A5FA.svg?style=flat-square&logo=Poetry&logoColor=white" alt="Poetry">
	<img src="https://img.shields.io/badge/Python-3776AB.svg?style=flat-square&logo=Python&logoColor=white" alt="Python">
	<img src="https://img.shields.io/badge/GitHub%20Actions-2088FF.svg?style=flat-square&logo=GitHub-Actions&logoColor=white" alt="GitHub%20Actions">
	<img src="https://img.shields.io/badge/Pytest-0A9EDC.svg?style=flat-square&logo=Pytest&logoColor=white" alt="Pytest">
	<img src="https://img.shields.io/badge/NumPy-013243.svg?style=flat-square&logo=NumPy&
    logoColor=white" alt="NumPy">
    <img src="https://img.shields.io/badge/SKlearn-013243.svg?style=flat-square&logo=scikit-learn&logoColor=white" alt="MLflow">
        
</p>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>

- [ Overview](#overview)
- [ Dependencies](#️dependencies)
- [ Installation](#installation)
  - [ Usage](#-usage)
  - [ Tests](#-tests)
- [ Contributing](#-contributing)
- [ License](#-license)
- [ Acknowledgments](#-acknowledgments)
</details>
<hr>

## Overview

ML-EXTRA is a project that aims to facilitate the development of Machine Learning models. Currently, the additional features provided by this package are MLflow-oriented. However, the tool may expand in the future and consider other frameworks. The core of this package is to provide a set of decorators that allow tracking different artifacts in a given experiment.

---

## Dependencies
* python = "^3.11"
* mlflow = "^2.12.1"
* dill = "^0.3.8"
* pytest = "^8.2.0"
* coverage = "^7.5.3"
* setuptools = "^70.0.0"

## Installation

```sh
pip -U install ml-extra
```
---

## 🤝 Contributing

Contributions are welcome! Here are several ways you can contribute:

- **[Report Issues](https://github.com/eli64s/readme-ai/issues)**: Submit bugs found or log feature requests for the `readme-ai` project.
- **[Submit Pull Requests](https://github.com/eli64s/readme-ai/blob/main/CONTRIBUTING.md)**: Review open PRs, and submit your own PRs.
- **[Join the Discussions](https://github.com/eli64s/readme-ai/discussions)**: Share your insights, provide feedback, or ask questions.

<summary>Contributing Guidelines</summary>
<details>

1. **Fork the Repository**: Start by forking the project repository to your github account.
2. **Clone Locally**: Clone the forked repository to your local machine using a git client.
   ```sh
   git clone https://github.com/eli64s/readme-ai
   ```
3. **Create a New Branch**: Always work on a new branch, giving it a descriptive name.
   ```sh
   git checkout -b new-feature-x
   ```
4. **Make Your Changes**: Develop and test your changes locally.
5. **Commit Your Changes**: Commit with a clear message describing your updates.
   ```sh
   git commit -m 'Implemented new feature x.'
   ```
6. **Push to github**: Push the changes to your forked repository.
   ```sh
   git push origin new-feature-x
   ```
7. **Submit a Pull Request**: Create a PR against the original project repository. Clearly describe the changes and their motivations.
8. **Review**: Once your PR is reviewed and approved, it will be merged into the main branch. Congratulations on your contribution!
</details>


---

## 📄 License

This project is protected under the [SELECT-A-LICENSE](https://choosealicense.com/licenses) License. For more details, refer to the [LICENSE](https://choosealicense.com/licenses/) file.

---

## 👏 Acknowledgments

- List any resources, contributors, inspiration, etc. here.

[**Return**](#-overview)

---