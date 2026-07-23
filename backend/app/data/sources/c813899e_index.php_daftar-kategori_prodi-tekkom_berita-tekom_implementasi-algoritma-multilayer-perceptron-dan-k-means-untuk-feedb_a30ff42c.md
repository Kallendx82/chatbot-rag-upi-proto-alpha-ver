# Implementation of Multilayer Perceptron and K-Means Algorithms for Instant Narrative Feedback in Program Learning Systems

> Source: https://kd-cibiru.upi.edu/index.php/daftar-kategori/prodi-tekkom/berita-tekom/implementasi-algoritma-multilayer-perceptron-dan-k-means-untuk-feedback-naratif-instan-pada-sistem-pembelajaran-program

Implementation of Multilayer Perceptron and K-Means Algorithms for Instant Narrative Feedback in Program Learning Systems
October 3, 2025
TEKKOM Admin
TEKKOM News
Implementation of Multilayer Perceptron and K-Means Algorithms for Instant Narrative Feedback in Program Learning Systems

The development of artificial intelligence (AI) technology has driven innovation in education, particularly in computer-based learning systems. One of the challenges in programming learning is how to provide fast, accurate, and narrative feedback on student work. This study proposes the implementation of a combination of the Multilayer Perceptron (MLP) algorithm and K-Means clustering to generate instant narrative feedback in a programming learning system. This approach aims to improve the student learning experience by providing automated feedback that includes not only grades but also textual descriptions of errors and areas for improvement.

1. Introduction

Conventional programming learning systems often rely on manual assessment or automated test case-based testing systems. However, these approaches only provide true/false results without explaining the context of the error. As a result, students struggle to understand the causes of their logical or syntactic errors.

The application of the Multilayer Perceptron (MLP) algorithm allows the system to learn code error patterns from a large dataset of previously collected student code. Meanwhile, the K-Means algorithm can group similar error types to facilitate the development of relevant feedback narratives. By combining these two algorithms, the system can provide instant feedback that is both descriptive and contextual.

2. Methodology
2.1. System Architecture

The system consists of three main components:

Source Code Preprocessing – student program code is converted into feature vector representation (e.g. based on syntax tokens, function frequencies, and control structures).

Error Classification using MLP – multilayer neural networks are used to predict error types (e.g., syntax errors, logic errors, or output errors).

Error Pattern Clustering with K-Means – classification results are grouped based on pattern similarity to find general trends in error types.

Narrative Feedback Generation – the system generates narrative sentences based on the classification and cluster results, using rule-based templates such as:

“Your program has a logic error in the loop. Please check the boundary conditions in the loop.”

“The syntax does not conform to Python language rules, note the indentation on line 12.”

2.2. Multilayer Perceptron (MLP) Algorithm

The MLP was used as a supervised learning model with input, hidden, and output layers. Each neuron in the hidden layer used a ReLU activation function to accelerate convergence. The model was trained using a dataset of student programs labeled with error types.

2.3. K-Means Algorithm

K-Means functions as an unsupervised clustering technique to group errors with similar characteristics. Each cluster represents a common pattern of a particular error, such as "global variable misuse" or "data type mismatch."

3. Results and Discussion

Experiments were conducted on a basic programming code dataset containing 5,000 examples from various students. The MLP model achieved an error classification accuracy of 92.4% , while K-Means successfully clustered error patterns with a silhouette score of 0.71 , indicating good cluster quality.

The system then generates instant narrative feedback, on average, in less than 1.5 seconds after the code is uploaded. Based on a trial of 50 students, 84% of respondents stated that the narrative feedback helped them understand errors and improve their code more quickly.

4. Conclusion

The combined implementation of MLP and K-Means in a programming learning system has proven effective in generating instant, informative, and personalized narrative feedback. This approach not only speeds up the evaluation process but also improves students' conceptual understanding of program logic.

For further research, the system can be developed with the integration of Natural Language Generation (NLG) based on large language models (LLM) to produce more natural and contextual feedback.

SDGs 4: Quality Education , SDGs 9: Industry, Innovation, and Infrastructure

Views: 192
Previous article: Congratulations and Success! The UPI Cibiru Mamah Prayer Team Wins Second Place in the Internet of Things Competition at the ITECHNO CUP 2025. Before
Next article: Design and Implementation of an Autonomous Semantic Hazard Mapping System on a Mobile Robot Following
FaLang translation system by Faboba
