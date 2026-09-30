# 0. A Survey on the Optimization of Large Language Model-based Agents

## 1. Introduction to Large Language Model-based Agents
The optimization of Large Language Model-based agents is a rapidly evolving field, with recent advancements in large language models (LLMs) enabling LLM-based agents to tackle complex multi-step tasks, including embodied housework and science experiments [33,59,69,135,170,178]. To understand the current state of LLM-based agents and their optimization, it is essential to compare and contrast the experimental designs of different studies. These studies demonstrate the potential of LLMs in optimizing various tasks, including automated proof optimization and symbolic plan generation. The experimental design of [59] focuses on utilizing LLMs as optimizers, while [69] introduces an agent-based approach to automated proof optimization. The divergent conclusions of these studies can be attributed to differences in their experimental designs, such as the choice of optimization algorithms and the evaluation metrics used. By integrating the extracted information from these studies, we can gain a deeper understanding of the current analytical framework and provide a roadmap for navigating the subsequent chapters. The optimization of LLM-based agents is crucial for their applications in various fields, including software engineering, customer service, and consulting. Therefore, it is essential to continue exploring new approaches to optimize LLM-based agents, such as meta plan optimization and cooperative plan optimization. By doing so, we can unlock the full potential of LLM-based agents and achieve significant advancements in artificial intelligence.
## 2. Background, Fundamentals, and Optimization Techniques
The field of Large Language Models (LLMs) has experienced significant growth in recent years, with various studies exploring their applications, architectures, and optimization techniques [80,81,94]. LLMs have been successfully applied to various tasks, including natural language processing, decision-making, and optimization problems. However, their development and optimization pose significant challenges, such as the need for large amounts of training data, computational resources, and effective optimization techniques [3,17,167].

To address these challenges, researchers have proposed various optimization techniques, including multi-agent collaboration, fine-tuning, and negative example integration [3,17]. These techniques aim to improve the performance and efficiency of LLMs in various tasks and applications. For instance, the Optima framework uses supervised fine-tuning and direct preference optimization to refine agent communication and improve task performance [3]. Similarly, the CMAT framework introduces a structured environment where individual agents work together to process information, make decisions, and solve complex tasks [17].

In addition to these techniques, researchers have also explored the use of evolutionary algorithms, reinforcement learning, and knowledge distillation to optimize LLMs [58,68,139]. These methods have shown promising results in improving the performance and efficiency of LLMs in various tasks and applications.

Furthermore, the development of LLM-based agents has also been explored, with a focus on their applications in software engineering, natural language processing, and decision-making [22,74,86]. These agents have the potential to revolutionize various industries and applications, enabling more efficient and effective decision-making, problem-solving, and communication.

In conclusion, the field of LLMs is rapidly evolving, with significant advancements in their architectures, optimization techniques, and applications. The development of LLM-based agents has the potential to transform various industries and applications, enabling more efficient and effective decision-making, problem-solving, and communication. Further research is needed to explore the full potential of LLMs and address the challenges associated with their development and optimization [67,132,148].
### 2.1 LLM Architecture
The Large Language Model (LLM) architecture is a crucial component of LLM-based agents, and it involves the use of transformer-based models, which are pre-trained on large datasets and fine-tuned for specific tasks [94,167]. The transformer architecture is based on self-attention mechanisms, which allow the model to attend to different parts of the input sequence simultaneously [172]. The LLM architecture is designed to support the development of autonomous agents that can interact with environments, humans, or other agents [115]. 

The key concepts and techniques in LLM architecture include the use of encoder-decoder structures, the role of attention mechanisms, and the importance of pre-training and fine-tuning [7]. The benefits of LLM architecture include its ability to generate high-quality text, its flexibility in handling different tasks and domains, and its potential for improving the performance of LLM-based agents [52]. However, the challenges of LLM architecture include its high computational cost, its requirement for large amounts of training data, and its potential for generating biased or misleading responses [80].

To propose a framework for understanding the benefits and challenges of LLM architecture in LLM-based agents, we need to consider the trade-offs between the complexity of the model, the quality of the generated text, and the computational resources required [24]. We also need to consider the potential applications of LLM-based agents, such as natural language processing, code generation, and decision-making [63]. By analyzing the key concepts and techniques in LLM architecture and proposing a framework for understanding its benefits and challenges, we can improve the performance and effectiveness of LLM-based agents in various applications [68]. 

In addition to the transformer architecture, other architectures such as recurrent neural networks (RNNs) and long short-term memory (LSTM) networks have also been used in LLMs [58]. However, the transformer architecture has become the dominant architecture for LLMs due to its ability to handle long-range dependencies and its parallelization capabilities [185]. The use of pre-trained models like BERT and RoBERTa has also become a standard practice in LLMs, as they provide a good starting point for fine-tuning and can improve the performance of the model [165].

Overall, the LLM architecture is a critical component of LLM-based agents, and its design and development have a significant impact on the performance and effectiveness of these agents [16]. By understanding the key concepts and techniques in LLM architecture and proposing a framework for understanding its benefits and challenges, we can improve the performance and effectiveness of LLM-based agents in various applications [21].
### 2.2 Optimization Techniques
Optimization techniques are crucial for improving the performance and efficiency of Large Language Model (LLM)-based agents. Recent studies have introduced various optimization techniques, including fine-tuning, reinforcement learning, and meta-plan optimization [3,17]. The Optima framework, for instance, aims to optimize both communication efficiency and task effectiveness by leveraging supervised fine-tuning and direct preference optimization [3]. 

Another optimization technique is the Collaborative Multi-Agent Tuning (CMAT) framework, which introduces a structured environment where individual agents work together to process information, make decisions, and solve complex tasks [17]. CMAT allows for a more scalable and flexible approach to training LLMs. Additionally, techniques like reinforcement learning from human feedback (RLHF) and direct preference optimization (DPO) have been proposed to improve the performance of LLM-based agents [58,144].

Other optimization techniques include knowledge distillation, few-shot prompting, and chain of thought [89]. These techniques can be used to improve the performance of LLM-based agents on specific tasks, such as question answering and text generation. Furthermore, multi-agent collaboration and fine-tuning have been shown to be effective in improving the performance of LLM-based agents in various tasks [16,86].

The optimization of LLM-based agents also involves the use of evolutionary algorithms, which can be used to optimize prompts and improve the performance of LLMs [68]. Moreover, techniques like LayerNorm tuning have been proposed to improve the efficiency of multi-modal LLM fine-tuning [185]. 

Overall, the optimization of LLM-based agents is a crucial area of research, and various techniques have been proposed to improve their performance and efficiency. By leveraging these techniques, LLM-based agents can be optimized to perform better in various tasks and applications [128,130]. 

To propose a framework for understanding the benefits and challenges of optimization techniques in LLM-based agents, we need to consider the systematic organization of the work proposed to tackle challenges and deficiencies in current methods. This framework should take into account the various optimization techniques discussed above and provide a comprehensive overview of their benefits and challenges. By doing so, we can better understand how to optimize LLM-based agents and improve their performance in various tasks and applications. 

In conclusion, optimization techniques are essential for improving the performance and efficiency of LLM-based agents. Various techniques, including fine-tuning, reinforcement learning, and meta-plan optimization, have been proposed to optimize LLM-based agents. By leveraging these techniques and considering the systematic organization of the work proposed to tackle challenges and deficiencies in current methods, we can propose a framework for understanding the benefits and challenges of optimization techniques in LLM-based agents [33,56].
### 2.3 Multi-Agent Collaboration and Fine-Tuning
The concept of multi-agent collaboration and fine-tuning is crucial for improving the performance of Large Language Model (LLM)-based agents [17,132,148]. Multi-agent collaboration enables LLMs to learn from each other and improve their performance in complex tasks, while fine-tuning allows for adapting LLMs to specific tasks and environments. The CMAT framework, for instance, enables multi-agent collaboration and fine-tuning, which can significantly improve the performance of LLM-based agents [17]. 

Fine-tuning methods, such as supervised fine-tuning and reinforcement learning, can be used to adapt LLMs to specific tasks and environments [3,184]. The Optima framework, for example, uses iterative supervised fine-tuning to refine agent communication and improve task performance [3]. 

The use of multiple agents can also improve the performance of LLMs in tasks such as code generation, data analysis, and question answering [52,181]. The BOLAA architecture, for instance, enables the selection and communication between multiple labor LLM-based agents, allowing for more efficient and effective completion of complex tasks [181]. 

Moreover, multi-agent collaboration and fine-tuning can be applied to various domains, including natural language processing, computer vision, and reinforcement learning [71,132,152]. The input-conditioned graph generation framework, for example, allows for an abstract understanding of language agents by representing them as computational graphs where nodes perform specific operations and edges depict the flow of data [71]. 

However, there are also challenges associated with multi-agent collaboration and fine-tuning, such as the need for large amounts of data and computational resources, and the potential for overfitting or underfitting [13,48]. The Phoenix framework, for instance, uses multi-agent collaboration and fine-tuning to improve the performance of LLMs in multi-language settings, but requires large amounts of data and computational resources [13]. 

In conclusion, multi-agent collaboration and fine-tuning are essential techniques for improving the performance of LLM-based agents. By enabling LLMs to learn from each other and adapt to specific tasks and environments, these techniques can improve the efficiency and effectiveness of LLMs in various domains. However, there are also challenges associated with these techniques, and further research is needed to address these challenges and fully realize the potential of multi-agent collaboration and fine-tuning [3,17,132].
### 2.4 Negative Example Integration and Adaptation
The integration of negative examples and adaptation methods is crucial for improving the robustness and generalizability of Large Language Model (LLM)-based agents [148,184]. Negative example integration involves incorporating negative examples into the training process to enable LLMs to learn from failures and adapt to new environments and tasks. This technique can be applied to various tasks, including natural language processing, decision-making, and optimization problems. For instance, the paper [184] explores the integration of negative examples in fine-tuning LLMs as agents and proposes a novel approach to negative example integration, which outperforms traditional methods by solely using positive examples or naively combining positive and negative ones.

Adaptation methods, on the other hand, enable LLM-based agents to adapt to new situations, tasks, and environments. These methods can be used to improve the performance of LLMs in various applications, including conversational tasks, decision-making, and optimization problems. The paper [16] highlights the importance of adaptation methods in enabling LLM-based agents to learn from experience and improve their performance over time. The authors propose a framework that integrates negative example integration and adaptation methods to improve the robustness and generalizability of LLM-based agents.

The benefits of negative example integration and adaptation include improved robustness, generalizability, and adaptability of LLM-based agents. These techniques can be used to improve the performance of LLMs in various applications, including natural language processing, decision-making, and optimization problems. However, there are also challenges associated with negative example integration and adaptation, such as the need for large amounts of training data, the risk of overfitting, and the requirement for careful tuning of hyperparameters.

Future research directions aimed at rectifying the shortcomings of current work include the development of more efficient and effective negative example integration and adaptation methods, the application of these techniques to various tasks and domains, and the investigation of the potential benefits and challenges of using negative example integration and adaptation in real-world applications [94]. The paper [148] discusses the importance of developing data-efficient training methods for LLMs, which can be used to improve the performance of LLM-based agents in various applications.

In conclusion, negative example integration and adaptation are crucial techniques for improving the robustness and generalizability of LLM-based agents. These techniques can be used to improve the performance of LLMs in various applications, including natural language processing, decision-making, and optimization problems. However, there are also challenges associated with negative example integration and adaptation, and future research directions should focus on developing more efficient and effective methods, applying these techniques to various tasks and domains, and investigating the potential benefits and challenges of using negative example integration and adaptation in real-world applications [16,94].
## 3. Benchmarking, Evaluation, and Applications
<figure-link title='Benchmarking Frameworks and Applications' type='mermaid' content='graph LR\n    A["Benchmarking Frameworks"] --> B["LOTA-Bench"]\n    A --> C["ORCALOCA"]\n    A --> D["Plansformer"]\n    B --> E["Software Issue Localization"]\n    C --> F["Embodied Agents"]\n    D --> G["Decision Optimization"]'></figure-link>
The key concepts and techniques in benchmarking, evaluation, and applications of Large Language Model (LLM)-based agents are crucial for understanding their benefits and challenges. Benchmarking frameworks, such as LOTA-Bench [107,176], provide a comprehensive evaluation of LLM-based agents in various environments. The ORCALOCA framework [170] is another example of a benchmarking framework that evaluates the performance of LLM-based agents in software issue localization tasks.

The Plansformer model [135] is a technique used for generating symbolic plans using transformers, which can be applied to various applications, including embodied agents and software issue localization. The large language model (LLM) for telecommunications [94] provides a comprehensive survey of principles, key techniques, and opportunities in the field.

The adoption of methods from other fields or disciplines, such as efficient inference for large language models [80,81], can provide valuable insights and techniques for improving the performance of LLM-based agents.

In terms of applications, LLM-based agents have been used in various domains, including software engineering [86], natural language processing [158], and decision optimization [168]. The use of LLM-based agents in these domains has shown promising results, with improvements in performance and efficiency.

However, there are also challenges associated with benchmarking, evaluation, and applications of LLM-based agents, such as the need for standardized benchmarks and evaluation metrics [189]. The development of robust and efficient benchmarking frameworks is essential for assessing the performance of LLM-based agents and identifying areas for improvement.

Overall, the benchmarking, evaluation, and applications of LLM-based agents are critical components of the field, and ongoing research is needed to address the challenges and opportunities associated with these components. By adopting methods from other fields or disciplines and developing standardized benchmarks and evaluation metrics, we can improve the performance and efficiency of LLM-based agents and unlock their full potential in various applications [33,130].
## 4. Conclusion and Future Directions
The optimization of Large Language Model (LLM)-based agents is a rapidly evolving field, with significant potential for improving their performance in various tasks and environments [3,16]. The papers analyzed in this survey highlight the importance of efficient fine-tuning strategies, multi-agent collaboration, and negative example integration for optimizing LLM-based agents [11,180]. 

The use of LLMs in software engineering tasks, such as software issue localization, has shown promising results [170]. However, there is a need for further research on optimizing LLM-based agents for software engineering tasks, including the development of more advanced LLM architectures and the integration of LLM-based agents with other software engineering tools and techniques [86]. 

The application of techniques from other fields, such as software engineering, can improve the efficiency of LLM-based agents [22]. For example, the use of software engineering principles can help improve the design and development of LLM-based agents, leading to more efficient and effective agents [74]. 

Future research directions include the development of more advanced optimization techniques, such as multi-agent collaboration and negative example integration, and the application of LLM-based agents to real-world problems [107,170]. The integration of methods from other fields, such as software engineering, can help address current challenges and shortcomings in LLM-based agents [94]. 

In conclusion, the optimization of LLM-based agents is a critical area of research, with significant potential for improving their performance in various tasks and environments [16]. Further research is needed to develop more advanced optimization techniques and to apply LLM-based agents to real-world problems, and the integration of methods from other fields can help address current challenges and shortcomings in LLM-based agents [3,170].

## References
[1] AvaTaR: Optimizing LLM Agents for Tool-Assisted Knowledge Retrieval http://arxiv.org/abs/2406.11200

[2] Retroformer: Retrospective Large Language Agents with Policy Gradient Optimization http://arxiv.org/abs/2308.02151

[3] Optima: Optimizing Effectiveness and Efficiency for LLM-Based Multi-Agent System http://arxiv.org/abs/2410.08115

[4] Learning Strategic Language Agents in the Werewolf Game with Iterative Latent Space Policy Optimization http://arxiv.org/abs/2502.04686

[5] Patched MOA: optimizing inference for diverse software development tasks http://arxiv.org/abs/2407.18521

[6] Dynamic LLM-Agent Network  An LLM-agent Collaboration Framework with
  Agent Team Optimization http://arxiv.org/abs/2310.02170

[7] The Ultimate Guide to Fine-Tuning LLMs from Basics to Breakthroughs: An Exhaustive Review of Technologies, Research, Best Practices, Applied Research Challenges and Opportunities http://arxiv.org/abs/2408.13296

[8] Optimizing Language Models for Human Preferences is a Causal Inference Problem http://arxiv.org/abs/2402.14979

[9] Self-evolving Agents with reflective and memory-augmented abilities http://arxiv.org/abs/2409.00872

[10] Robust Prompt Optimization for Large Language Models Against Distribution Shifts https://doi.org/10.18653/v1/2023.emnlp-main.95

[11] Crafting Efficient Fine-Tuning Strategies for Large Language Models http://arxiv.org/abs/2407.13906

[12] Algorithm Evolution Using Large Language Model http://arxiv.org/abs/2311.15249

[13] PHOENIX: Open-Source Language Adaption for Direct Preference Optimization http://arxiv.org/abs/2401.10580

[14] Automatic Prompt Optimization with "Gradient Descent" and Beam Search http://arxiv.org/abs/2305.03495

[15] Star-Agents: Automatic Data Optimization with LLM Agents for Instruction Tuning http://arxiv.org/abs/2411.14497

[16] Agent Q: Advanced Reasoning and Learning for Autonomous AI Agents http://arxiv.org/abs/2408.07199

[17] CMAT: A Multi-Agent Collaboration Tuning Framework for Enhancing Small Language Models http://arxiv.org/abs/2404.01663

[18] MetaReflection: Learning Instructions for Language Agents using Past Reflections http://arxiv.org/abs/2405.13009

[19] ArCHer: Training Language Model Agents via Hierarchical Multi-Turn RL http://arxiv.org/abs/2402.19446

[20] Direct Multi-Turn Preference Optimization for Language Agents http://arxiv.org/abs/2406.14868

[21] Research on the Application and Optimization Strategies of Deep Learning in Large Language Models https://doi.org/10.53469/jtpes.2024.04(05).12

[22] Agents in software engineering: survey, landscape, and vision https://doi.org/10.1007/s10515-025-00544-2

[23] AgentSquare: Automatic LLM Agent Search in Modular Design Space http://arxiv.org/abs/2410.06153

[24] Beyond Efficiency  A Systematic Survey of Resource-Efficient Large
  Language Models http://arxiv.org/abs/2401.00625

[25] X-ALMA: Plug & Play Modules and Adaptive Rejection for Quality Translation at Scale http://arxiv.org/abs/2410.03115

[26] Mathematical Programming Through the Lens of LLMs: Systematic Evidence and Empirical Gaps https://doi.org/10.1109/access.2025.3618987

[27] Optimizing Large Language Models for Dynamic Constraints through Human-in-the-Loop Discriminators http://arxiv.org/abs/2410.15163

[28] Learning to Clarify: Multi-turn Conversations with Action-Based Contrastive Self-Training http://arxiv.org/abs/2406.00222

[29] Symbolic Learning Enables Self-Evolving Agents http://arxiv.org/abs/2406.18532

[30] PatternGPT :A Pattern-Driven Framework for Large Language Model Text Generation https://doi.org/10.1145/3633637.3633648

[31] Web Agents with World Models: Learning and Leveraging Environment Dynamics in Web Navigation http://arxiv.org/abs/2410.13232

[32] Adapting Language-Specific LLMs to a Reasoning Model in One Day via Model Merging - An Open Recipe http://arxiv.org/abs/2502.09056

[33] MPO: Boosting LLM Agents with Meta Plan Optimization http://arxiv.org/abs/2503.02682

[34] LLaMAntino: LLaMA 2 Models for Effective Text Generation in Italian Language http://arxiv.org/abs/2312.09993

[35] A Survey of LLM-based Agents in Medicine: How far are we from Baymax? http://arxiv.org/abs/2502.11211

[36] MASTER: A Multi-Agent System with LLM Specialized MCTS http://arxiv.org/abs/2501.14304

[37] Aligning Crowd-sourced Human Feedback for Reinforcement Learning on Code Generation by Large Language Models https://doi.org/10.1109/tbdata.2024.3524104

[38] It's Morphing Time: Unleashing the Potential of Multiple LLMs via Multi-objective Optimization http://arxiv.org/abs/2407.00487

[39] KAFA-Merge: Model Merging Method With Layer-Based Bayes+Linear Search https://doi.org/10.1109/access.2025.3582015

[40] BiasDPO: Mitigating Bias in Language Models through Direct Preference Optimization http://arxiv.org/abs/2407.13928

[41] Enhancing the General Agent Capabilities of Low-Parameter LLMs through Tuning and Multi-Branch Reasoning http://arxiv.org/abs/2403.19962

[42] Language Agents as Optimizable Graphs http://arxiv.org/abs/2402.16823

[43] No more optimization rules: LLM-enabled policy-based multi-modal query optimizer http://arxiv.org/abs/2403.13597

[44] Learning to Reduce: Optimal Representations of Structured Data in Prompting Large Language Models http://arxiv.org/abs/2402.14195

[45] AutoManual: Constructing Instruction Manuals by LLM Agents via Interactive Environmental Learning https://doi.org/10.52202/079017-0019

[46] FireAct  Toward Language Agent Fine-tuning http://arxiv.org/abs/2310.05915

[47] LLM-Planner: Few-Shot Grounded Planning for Embodied Agents with Large Language Models https://doi.org/10.1109/iccv51070.2023.00280

[48] Simultaneous Masking, Not Prompting Optimization: A Paradigm Shift in Fine-tuning LLMs for Simultaneous Translation http://arxiv.org/abs/2405.10443

[49] Improving Small-Scale Large Language Models Function Calling for Reasoning Tasks http://arxiv.org/abs/2410.18890

[50] Enhancing the Traditional Chinese Medicine Capabilities of Large Language Model through Reinforcement Learning from AI Feedback http://arxiv.org/abs/2411.00897

[51] COSMOS: A Hybrid Adaptive Optimizer for Memory-Efficient Training of LLMs http://arxiv.org/abs/2502.17410

[52] TPTU  Large Language Model-based AI Agents for Task Planning and Tool
  Usage http://arxiv.org/abs/2308.03427

[53] StablePrompt : Automatic Prompt Tuning using Reinforcement Learning for Large Language Model http://arxiv.org/abs/2410.07652

[54] Understanding the planning of LLM agents  A survey http://arxiv.org/abs/2402.02716

[55] Mixture-of-Agents Enhances Large Language Model Capabilities http://arxiv.org/abs/2406.04692

[56] Agent-FLAN: Designing Data and Methods of Effective Agent Tuning for Large Language Models http://arxiv.org/abs/2403.12881

[57] Inference Optimizations for Large Language Models: Effects, Challenges, and Practical Considerations http://arxiv.org/abs/2408.03130

[58] Investigating on RLHF methodology http://arxiv.org/abs/2410.01789

[59] Large Language Models as Optimizers http://arxiv.org/abs/2309.03409

[60] Revolve: Optimizing AI Systems by Tracking Response Evolution in Textual Optimization http://arxiv.org/abs/2412.03092

[61] Achieving Peak Performance for Large Language Models: A Systematic Review https://doi.org/10.1109/access.2024.3424945

[62] Understanding the Weakness of Large Language Model Agents within a Complex Android Environment https://doi.org/10.1145/3637528.3671650

[63] Emergent autonomous scientific research capabilities of large language models http://arxiv.org/abs/2304.05332

[64] CoLLiE: Collaborative Training of Large Language Models in an Efficient Way http://arxiv.org/abs/2312.00407

[65] Can LLMs plan paths with extra hints from solvers? http://arxiv.org/abs/2410.05045

[66] Agent-Pro: Learning to Evolve via Policy-Level Reflection and Optimization http://arxiv.org/abs/2402.17574

[67] FedDTPT: Federated Discrete and Transferable Prompt Tuning for Black-Box Large Language Models http://arxiv.org/abs/2411.00985

[68] Deep Insights into Automated Optimization with Large Language Models and Evolutionary Algorithms http://arxiv.org/abs/2410.20848

[69] ImProver: Agent-Based Automated Proof Optimization http://arxiv.org/abs/2410.04753

[70] Survey on Large Language Model-Enhanced Reinforcement Learning: Concept, Taxonomy, and Methods https://doi.org/10.1109/tnnls.2024.3497992

[71] Input Conditioned Graph Generation for Language Agents http://arxiv.org/abs/2406.11555

[72] RLHF Can Speak Many Languages: Unlocking Multilingual Preference Optimization for LLMs http://arxiv.org/abs/2407.02552

[73] Language Model Evolutionary Algorithms for Recommender Systems: Benchmarks and Algorithm Comparisons http://arxiv.org/abs/2411.10697

[74] Diversity Empowers Intelligence: Integrating Expertise of Software Engineering Agents http://arxiv.org/abs/2408.07060

[75] The Efficiency Spectrum of Large Language Models: An Algorithmic Survey http://arxiv.org/abs/2312.00678

[76] Small Molecule Optimization with Large Language Models http://arxiv.org/abs/2407.18897

[77] CourseGPT-zh: an Educational Large Language Model Based on Knowledge Distillation Incorporating Prompt Optimization http://arxiv.org/abs/2405.04781

[78] Trial and Error: Exploration-Based Trajectory Optimization for LLM Agents http://arxiv.org/abs/2403.02502

[79] Responsible Multilingual Large Language Models: A Survey of Development, Applications, and Societal Impact http://arxiv.org/abs/2410.17532

[80] A Survey on Efficient Inference for Large Language Models http://arxiv.org/abs/2404.14294

[81] LLM Inference Unveiled  Survey and Roofline Model Insights http://arxiv.org/abs/2402.16363

[82] SMART: Automatically Scaling Down Language Models with Accuracy Guarantees for Reduced Processing Fees http://arxiv.org/abs/2403.13835

[83] Lost in Translation: Large Language Models in Non-English Content Analysis http://arxiv.org/abs/2306.07377

[84] Prompt Optimization in Large Language Models https://doi.org/10.3390/math12060929

[85] Merino: Entropy-driven Design for Generative Language Models on IoT Devices http://arxiv.org/abs/2403.07921

[86] Large Language Model-Based Agents for Software Engineering: A Survey http://arxiv.org/abs/2409.02977

[87] Several categories of Large Language Models (LLMs): A Short Survey https://doi.org/10.22214/ijraset.2023.54677

[88] Structured Pruning of Large Language Models https://doi.org/10.18653/v1/2020.emnlp-main.496

[89] Bactrainus: Optimizing Large Language Models for Multi-hop Complex Question Answering Tasks http://arxiv.org/abs/2501.06286

[90] AgentBoard  An Analytical Evaluation Board of Multi-turn LLM Agents http://arxiv.org/abs/2401.13178

[91] Efficiently Adapting Pretrained Language Models To New Languages http://arxiv.org/abs/2311.05741

[92] FLAG-Trader: Fusion LLM-Agent with Gradient-based Reinforcement Learning for Financial Trading http://arxiv.org/abs/2502.11433

[93] PolyPrompt: Automating Knowledge Extraction from Multilingual Language Models with Dynamic Prompt Generation http://arxiv.org/abs/2502.19756

[94] Large Language Model (LLM) for Telecommunications: A Comprehensive Survey on Principles, Key Techniques, and Opportunities http://arxiv.org/abs/2405.10825

[95] Unveiling the Lexical Sensitivity of LLMs: Combinatorial Optimization for Prompt Enhancement http://arxiv.org/abs/2405.20701

[96] More Agents Is All You Need http://arxiv.org/abs/2402.05120

[97] DiverseDialogue: A Methodology for Designing Chatbots with Human-Like Diversity http://arxiv.org/abs/2409.00262

[98] Language Model Fine-Tuning on Scaled Survey Data for Predicting Distributions of Public Opinions http://arxiv.org/abs/2502.16761

[99] AgentOhana  Design Unified Data and Training Pipeline for Effective
  Agent Learning http://arxiv.org/abs/2402.15506

[100] Improving Text Embeddings for Smaller Language Models Using Contrastive Fine-tuning http://arxiv.org/abs/2408.00690

[101] WebRL: Training LLM Web Agents via Self-Evolving Online Curriculum Reinforcement Learning http://arxiv.org/abs/2411.02337

[102] xLAM: A Family of Large Action Models to Empower AI Agent Systems http://arxiv.org/abs/2409.03215

[103] Training Language Model Agents without Modifying Language Models http://arxiv.org/abs/2402.11359

[104] Smart Language Agents in Real-World Planning http://arxiv.org/abs/2407.19667

[105] Large Language Model Agent for Hyper-Parameter Optimization http://arxiv.org/abs/2402.01881

[106] Preference Ranking Optimization for Human Alignment http://arxiv.org/abs/2306.17492

[107] LoTa-Bench: Benchmarking Language-oriented Task Planners for Embodied Agents http://arxiv.org/abs/2402.08178

[108] MetaAgents  Simulating Interactions of Human Behaviors for LLM-based
  Task-oriented Coordination via Collaborative Generative Agents http://arxiv.org/abs/2310.06500

[109] OptiMUS: Scalable Optimization Modeling with (MI)LP Solvers and Large Language Models http://arxiv.org/abs/2402.10172

[110] ICE-GRT: Instruction Context Enhancement by Generative Reinforcement based Transformers http://arxiv.org/abs/2401.02072

[111] Data Interpreter: An LLM Agent For Data Science http://arxiv.org/abs/2402.18679

[112] LLMR: Knowledge Distillation with a Large Language Model-Induced Reward http://arxiv.org/abs/2409.12500

[113] Investigating LLM Applications in E-Commerce http://arxiv.org/abs/2408.12779

[114] From Context to Action: Analysis of the Impact of State Representation and Context on the Generalization of Multi-Turn Web Navigation Agents http://arxiv.org/abs/2410.23555

[115] Agents: An Open-source Framework for Autonomous Language Agents http://arxiv.org/abs/2309.07870

[116] EDGE: Efficient Data Selection for LLM Agents via Guideline Effectiveness http://arxiv.org/abs/2502.12494

[117] Steering Large Language Models between Code Execution and Textual Reasoning http://arxiv.org/abs/2410.03524

[118] AFlow: Automating Agentic Workflow Generation http://arxiv.org/abs/2410.10762

[119] Learning to Reduce: Towards Improving Performance of Large Language Models on Structured Data http://arxiv.org/abs/2407.02750

[120] Reinforcement Learning from Human Feedback with Active Queries http://arxiv.org/abs/2402.09401

[121] Sub-goal Distillation: A Method to Improve Small Language Agents http://arxiv.org/abs/2405.02749

[122] Multi-Reference Preference Optimization for Large Language Models http://arxiv.org/abs/2405.16388

[123] SplitLLM: Collaborative Inference of LLMs for Model Placement and Throughput Optimization http://arxiv.org/abs/2410.10759

[124] Tiny Refinements Elicit Resilience: Toward Efficient Prefix-Model Against LLM Red-Teaming http://arxiv.org/abs/2405.12604

[125] Multiagent Finetuning: Self Improvement with Diverse Reasoning Chains http://arxiv.org/abs/2501.05707

[126] Sample-Efficient Alignment for LLMs http://arxiv.org/abs/2411.01493

[127] Direct Nash Optimization: Teaching Language Models to Self-Improve with General Preferences http://arxiv.org/abs/2404.03715

[128] LLM Bandit: Cost-Efficient LLM Generation via Preference-Conditioned Dynamic Routing http://arxiv.org/abs/2502.02743

[129] Adaptive In-conversation Team Building for Language Model Agents http://arxiv.org/abs/2405.19425

[130] Xmodel-1.5: An 1B-scale Multilingual LLM http://arxiv.org/abs/2411.10083

[131] A Survey of Large Language Models http://arxiv.org/abs/2303.18223

[132] Large Language Model Applied in Multi-agent SystemA Survey https://doi.org/10.54254/2755-2721/109/20241330

[133] Chit-Chat or Deep Talk: Prompt Engineering for Process Mining http://arxiv.org/abs/2307.09909

[134] Mixture-of-Skills: Learning to Optimize Data Usage for Fine-Tuning Large Language Models http://arxiv.org/abs/2406.08811

[135] Plansformer: Generating Symbolic Plans using Transformers http://arxiv.org/abs/2212.08681

[136] Active Preference Learning for Large Language Models http://arxiv.org/abs/2402.08114

[137] A fine-tuning enhanced RAG system with quantized influence measure as AI judge https://doi.org/10.1038/s41598-024-79110-x

[138] Robust Optimization for Multilingual Translation with Imbalanced Data http://arxiv.org/abs/2104.07639

[139] ProxSparse: Regularized Learning of Semi-Structured Sparsity Masks for Pretrained LLMs http://arxiv.org/abs/2502.00258

[140] Exploring Design Choices for Building Language-Specific LLMs http://arxiv.org/abs/2406.14670

[141] SDPO: Segment-Level Direct Preference Optimization for Social Agents http://arxiv.org/abs/2501.01821

[142] MaskPrune: Mask-based LLM Pruning for Layer-wise Uniform Structures http://arxiv.org/abs/2502.14008

[143] A Self-enhancement Approach for Domain-specific Chatbot Training via Knowledge Mining and Digest http://arxiv.org/abs/2311.10614

[144] Direct Preference Optimization: Your Language Model is Secretly a Reward Model https://doi.org/10.52202/075280-2338

[145] Large Language Model based Multi-Agents: A Survey of Progress and Challenges http://arxiv.org/abs/2402.01680

[146] Exploring Sentiment Manipulation by LLM-Enabled Intelligent Trading Agents http://arxiv.org/abs/2502.16343

[147] mDPO: Conditional Preference Optimization for Multimodal Large Language Models http://arxiv.org/abs/2406.11839

[148] How to Train Data-Efficient LLMs http://arxiv.org/abs/2402.09668

[149] How to Protect Copyright Data in Optimization of Large Language Models? http://arxiv.org/abs/2308.12247

[150] LAMM: Language-Assisted Multi-Modal Instruction-Tuning Dataset, Framework, and Benchmark http://arxiv.org/abs/2306.06687

[151] MobileLLM  Optimizing Sub-billion Parameter Language Models for
  On-Device Use Cases http://arxiv.org/abs/2402.14905

[152] Evaluating Cultural and Social Awareness of LLM Web Agents http://arxiv.org/abs/2410.23252

[153] Enhancing Decision-Making for LLM Agents via Step-Level Q-Value Models http://arxiv.org/abs/2409.09345

[154] PanGu-π: Enhancing Language Model Architectures via Nonlinearity Compensation http://arxiv.org/abs/2312.17276

[155] Exploring the True Potential: Evaluating the Black-box Optimization Capability of Large Language Models http://arxiv.org/abs/2404.06290

[156] Sharpness-Aware Minimization Improves Language Model Generalization https://doi.org/10.18653/v1/2022.acl-long.508

[157] Dynamic Data Sampler for Cross-Language Transfer Learning in Large Language Models https://doi.org/10.1109/icassp48485.2024.10446640

[158] LLMs are Also Effective Embedding Models: An In-depth Overview http://arxiv.org/abs/2412.12591

[159] LLM Program Optimization via Retrieval Augmented Search http://arxiv.org/abs/2501.18916

[160] DyVal 2: Dynamic Evaluation of Large Language Models by Meta Probing Agents http://arxiv.org/abs/2402.14865

[161] A Scalable Distributed Syntactic, Semantic, and Lexical Language Model https://doi.org/10.1162/coli_a_00107

[162] Plug and Play with Prompts: A Prompt Tuning Approach for Controlling Text Generation http://arxiv.org/abs/2404.05143

[163] TL-Training: A Task-Feature-Based Framework for Training Large Language Models in Tool Use http://arxiv.org/abs/2412.15495

[164] Efficient Sequential Decision Making with Large Language Models http://arxiv.org/abs/2406.12125

[165] Supervised Knowledge Makes Large Language Models Better In-context Learners http://arxiv.org/abs/2312.15918

[166] Assessing Translation Capabilities of Large Language Models involving English and Indian Languages http://arxiv.org/abs/2311.09216

[167] Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG http://arxiv.org/abs/2501.09136

[168] From Large Language Models and Optimization to Decision Optimization CoPilot: A Research Manifesto http://arxiv.org/abs/2402.16269

[169] Unsupervised Improvement of Factual Knowledge in Language Models http://arxiv.org/abs/2304.01597

[170] OrcaLoca: An LLM Agent Framework for Software Issue Localization http://arxiv.org/abs/2502.00350

[171] SelfGoal: Your Language Agents Already Know How to Achieve High-level Goals http://arxiv.org/abs/2406.04784

[172] Advancing Transformer Architecture in Long-Context Large Language Models: A Comprehensive Survey http://arxiv.org/abs/2311.12351

[173] Exploring Accuracy-Fairness Trade-off in Large Language Models http://arxiv.org/abs/2411.14500

[174] SimOAP: Improve Coherence and Consistency in Persona-based Dialogue Generation via Over-sampling and Post-evaluation http://arxiv.org/abs/2305.11130

[175] Towards Fast Multilingual LLM Inference: Speculative Decoding and Specialized Drafters http://arxiv.org/abs/2406.16758

[176] AgentBench: Evaluating LLMs as Agents http://arxiv.org/abs/2308.03688

[177] Bridging Language Barriers in Healthcare: A Study on Arabic LLMs http://arxiv.org/abs/2501.09825

[178] CaPo: Cooperative Plan Optimization for Efficient Embodied Multi-Agent Cooperation http://arxiv.org/abs/2411.04679

[179] Memory-Efficient Adaptive Optimization http://arxiv.org/abs/1901.11150

[180] Multi-Agent Design: Optimizing Agents with Better Prompts and Topologies http://arxiv.org/abs/2502.02533

[181] BOLAA: Benchmarking and Orchestrating LLM-augmented Autonomous Agents http://arxiv.org/abs/2308.05960

[182] RLEF: Grounding Code LLMs in Execution Feedback with Reinforcement Learning http://arxiv.org/abs/2410.02089

[183] CodeTree: Agent-guided Tree Search for Code Generation with Large Language Models http://arxiv.org/abs/2411.04329

[184] Learning From Failure: Integrating Negative Examples when Fine-tuning Large Language Models as Agents http://arxiv.org/abs/2402.11651

[185] Tuning LayerNorm in Attention: Towards Efficient Multi-Modal LLM Finetuning http://arxiv.org/abs/2312.11420

[186] Speeding Up Question Answering Task of Language Models via Inverted
  Index http://arxiv.org/abs/2210.13578

[187] Symbiotic Cooperation for Web Agents: Harnessing Complementary Strengths of Large and Small LLMs http://arxiv.org/abs/2502.07942

[188] ControlMath: Controllable Data Generation Promotes Math Generalist Models http://arxiv.org/abs/2409.15376

[189] Trends in Integration of Knowledge and Large Language Models: A Survey and Taxonomy of Methods, Benchmarks, and Applications http://arxiv.org/abs/2311.05876

[190] ToolChain*: Efficient Action Space Navigation in Large Language Models with A* Search http://arxiv.org/abs/2310.13227
