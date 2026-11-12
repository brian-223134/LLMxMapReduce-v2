# LLMxMapReduce: Simplified Long-Sequence Processing using Large Language Models

<a href='https://surveygo.modelbest.cn/'><img src='https://img.shields.io/badge/Demo-Page-pink'></a> <a href='https://arxiv.org/abs/2410.09342'><img src='https://img.shields.io/badge/V1-Paper-Green'></a> <a href='https://arxiv.org/abs/2504.05732'><img src='https://img.shields.io/badge/V2-Paper-blue'></a> <a href='https://huggingface.co/datasets/R0k1e/SurveyEval'><img src='https://img.shields.io/badge/SurveyEval-Benchmark-yellow'></a> <a href='README_zh.md'><img src='https://img.shields.io/badge/Chinese-Readme-red'></a>

# 🔧 이 fork 에서 실행하기 (KISTI same-corpus 재현)

> 이 절은 fork 전용 메모입니다. 아래 upstream 문서(Getting Started 이후)는 원본 그대로 둡니다.
> 파이프라인 코드(`src/`)는 건드리지 않고, 요청 래퍼(`LLMxMapReduce_V2/request/openai.py`)의 env-gated 오버라이드와
> `scripts/`·`tests/` 만 추가했습니다. env 를 비우면 원본 동작입니다.

## 1. 새로 클론했을 때

```bash
git clone git@github.com:brian-223134/LLMxMapReduce-v2.git && cd LLMxMapReduce-v2
conda create -n llmxmr python=3.11 && conda activate llmxmr
pip install -r LLMxMapReduce_V2/requirements.txt
python -c "import nltk; nltk.download('punkt_tab')"      # 평가용. 받은 경로를 .env 의 NLTK_DATA 에

cp .env.example .env && chmod 600 .env                     # 키를 넣는다. .env·.env.* 는 .gitignore
# 유닛 테스트 (네트워크·GPU·키 불필요)
PYTHONPATH=LLMxMapReduce_V2 python -m unittest discover -s tests -v
```

- Stage 1·2(pool 검색·입력 생성)와 stage3 래퍼는 별도 저장소 `kisti_data` 의 `adapter/llmxmapreduce/run_stages.sh` 가 돕니다.
  이 스크립트는 경로가 하드코딩돼 있으니(`MR`, `AS`, `ENVS`, `KISTI_DATA_ROOT`) 다른 머신에서는 먼저 맞추세요.
  conda env 는 `llmxmr`(stage3), `autosurvey`(stage1, GPU), `asg-corpus`(stage2·검사 스크립트) 세 개를 씁니다.
- 원문이 든 jsonl·로그·진단 덤프는 git 에 없습니다 (`.gitignore`). 클론에는 manifest·ceiling·검사 결과 json 과 실험 기록(`docs/experiments/`)만 있습니다.

## 2. 백본 프로파일과 전환

백본은 **`.env`(엔드포인트·키·디코딩) + `--config_file`(모델 id)** 두 곳이 같이 바뀌어야 합니다. 한쪽만 바꾸면
OpenRouter 에 qwen id 를 보내거나 DashScope 에 llama id 를 보내 실패합니다.

| | A. OpenRouter · llama (**기본 / 원래**) | B. DashScope · qwen-plus (kisti-2608-r7 파일럿) |
|---|---|---|
| 모델 | `meta-llama/llama-3.3-70b-instruct` | `qwen-plus-2025-12-01` |
| config | `config/model_config_llama.json` (run_stages.sh 기본값) | `config/model_config_qwen.json` |
| `OPENAI_API_BASE` | `https://openrouter.ai/api/v1` | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` |
| `LLMXMR_PROVIDER` | `akashml/fp8` | (비움) |
| `LLMXMR_TRACK_COST` | `1` (usage.cost 로 실제 비용) | `0` |
| `LLMXMR_PRICE_IN` / `_OUT` | (비움) | `0.4` / `1.2` (토큰 기반 추정 비용) |
| `LLMXMR_TEMPERATURE` / `LLMXMR_MAX_TOKENS` | `0.6` / `8192` | `0.6` / `8192` |

두 프로파일 모두 `.env.example` 에 있습니다 (A 활성, B 는 파일 끝에 주석).

**A → B (qwen 으로 전환)**

```bash
cp -p .env .env.bak-openrouter-$(date +%Y%m%d)            # 원래 .env 보존 (.env.* 도 gitignore)
# .env 에서 OPENAI_API_KEY/BASE 를 DashScope 값으로, 나머지는 위 표 B 열로 고친다
K=/data2/chanjoong/kisti_data; S=$K/adapter/llmxmapreduce/run_stages.sh; export KISTI_VIEW=kisti-2608-r7
$S stage3 --config_file ./config/model_config_qwen.json   # 뒤에 준 인자가 run_stages.sh 의 llama config 를 덮는다
```

**B → A (원래대로 되돌리기)**

```bash
cp -p .env.bak-openrouter-20261111 .env                    # 이 서버의 백업. 새 클론이면 .env.example 의 A 블록으로 다시 작성
$S stage3                                                  # --config_file 을 빼면 model_config_llama.json
```

코드는 되돌릴 것이 없습니다 — DashScope 지원(`data_inspection_failed` 즉시 실패, 토큰 기반 추정 비용)과 진단 덤프는
모두 env 가 비어 있으면 동작하지 않거나 OpenRouter 응답에서 발동하지 않습니다.
되돌린 뒤 확인: `scripts/run_manifest.py` 가 만든 manifest 의 `profile.OPENAI_API_BASE`·`models` 가 A 값인지 봅니다.

## 3. 실행 순서 (view 하나, topic 하나 기준)

```bash
K=/data2/chanjoong/kisti_data; S=$K/adapter/llmxmapreduce/run_stages.sh; export KISTI_VIEW=kisti-2608-r7; D=data/$KISTI_VIEW
CUDA_VISIBLE_DEVICES=3 $S stage1 --topics $D/topics.pilot.jsonl     # topic 별 GT 공개일 cutoff 정책 필수
$S stage2 --only_title "<topic 전체 제목>"
$S stage3 [--config_file ./config/model_config_qwen.json]          # 저장되면 자동 종료 (AUTO_STOP=0 이면 수동)
python scripts/run_manifest.py --log $D/log/stage3.log --output_jsonl $D/output.jsonl --input_jsonl $D/input.jsonl \
    --pools $D/pools.jsonl --pool_ceiling $D/pool_ceiling.json --run_name <이름> --out data/manifest/<이름>.json
```

검사(`pool_ceiling`·`leak_check`·`ref_time_check`·`gt_recall`)와 view 별 경로는 `docs/experiments/kisti-2608-r4.md` §5 를 따릅니다.
`KISTI_VIEW` 기본값은 `kisti-2512` 이므로 항상 명시하세요.

## 4. 진단과 알려진 문제

- **잘린 응답 덤프**: `LLMXMR_DUMP_DIR=<dir>` 를 주면 `finish_reason=length` 응답을 프롬프트와 함께 저장합니다
  (`LLMXMR_DUMP_MIN_COMPLETION=<n>` 이면 긴 정상 응답도). 프롬프트 원문이 들어가므로 커밋 금지.
- **stage3 hung**: 로그에 `this was the 20th` / `RetryError ... TruncatedResponseError` 가 보이면 survey 가 소멸한 뒤
  프로세스만 살아 있는 상태입니다(호출 0, 자동 종료 안 됨). `$D/log/stage3.pid` 로 직접 종료하세요.
  r7 llm-watermarking 은 qwen-plus 가 ModifyOutline 에서 8192 토큰 반복 루프에 빠져 이렇게 실패했습니다
  (`data/manifest/stage3-2608-r7-llm-watermarking.failed.json`).
- **DashScope `429 BudgetLimitExceeded`**: rate limit 이 아니라 계정 예산 소진입니다. 재시도가 계속 두드리므로 즉시 멈추세요.
  rate limit 횟수는 `Rate limit exceeded` 로 셉니다 (`429` grep 은 밀리초 타임스탬프 오탐).

# 🎉 News
- [x] **`2025.09.13`** Release the code for LLMxMapReduce-V3.
- [x] **`2025.04.22`** Release [SurveyGO](https://surveygo.znyx.com.cn/), an online writting system driven by LLMxMapReduce-V2.
- [x] **`2025.04.09`** Release the paper of LLMxMapReduce-V2 in [arXiv](https://arxiv.org/abs/2504.05732).
- [x] **`2025.02.21`** Add support for both OpenAI API and OpenAI-compatible APIs (e.g., vLLM).
- [x] **`2024.10.12`** Release the paper of LLMxMapReduce-V1 in [arXiv](https://arxiv.org/abs/2410.09342).
- [x] **`2024.09.12`** Release the code for LLMxMapReduce-V1.

# 📚 Overview
**LLMxMapReduce** is a divide-and-conquer framework designed to enhance modern large language models (LLMs) in understanding and generating long sequences. Developed collaboratively by **AI9STARS**, **OpenBMB**, and **THUNLP**, this framework draws inspiration from the classic MapReduce algorithm introduced in the field of big data. Our goal is to build an LLM-driven distributed computing system capable of efficiently processing long sequences. Here are the main versions of LLMxMapReduce:

* [**LLMxMapReduce-V2**](https://github.com/thunlp/LLMxMapReduce/tree/main/LLMxMapReduce_V2): Introduces an entropy-driven convolutional test-time scaling mechanism to improve the integration of extremely large volumes of information, powering the online [SurveyGO](https://surveygo.modelbest.cn/) system.
* [**LLMxMapReduce-V3**](https://github.com/thunlp/LLMxMapReduce/blob/main/LLMxMapReduce_V3): Introduces an interactive, modular, and self-organized multi-agent system for academic survey generation.

# 📖 Introduction


Long-form generation is crucial for a wide range of practical applications, typically categorized into short-to-long and long-to-long generation. While short-to-long generations have received considerable attention, generating long texts from extremely long resources remains relatively underexplored. The primary challenge in long-to-long generation lies in effectively integrating and analyzing relevant information from extensive inputs, which remains difficult for current large language models (LLMs). In this paper, we propose LLMxMapReduce-V2, a novel test-time scaling strategy designed to enhance the ability of LLMs to process extremely long inputs. Drawing inspiration from convolutional neural networks, which iteratively integrate local features into higher-level global representations, LLMxMapReduce-V2 utilizes stacked convolutional scaling layers to progressively expand the understanding of input materials. Both quantitative and qualitative experimental results demonstrate that our approach substantially enhances the ability of LLMs to process long inputs and generate coherent, informative long-form articles, outperforming several representative baselines.

<div align="center">
  <img src="assets/main_pic.jpg" alt="$\text{LLM}\times \text{MapReduce}$-V2 framework">
</div>

# ⚡️ Getting Started
The following steps are about LLMxMapReduce-V2. If you want to use LLMxMapReduce-V3, you need to refer to [here](LLMxMapReduce_V3/README.md). 

To get started, ensure all dependencies listed in requirements.txt are installed. You can do this by running:
```bash
cd LLMxMapReduce_V2
conda create -n llm_mr_v2 python=3.11
conda activate llm_mr_v2
pip install -r requirements.txt
python -m playwright install --with-deps chromium
```

Before evaluation, you need to download punkt_tab firstly.
```python
import nltk
nltk.download('punkt_tab')
```
## Env config
Please set your OPENAI_API_KEY and OPENAI_API_BASE in your environment variables before start the pipeline. If you use miniconda, replace `anaconda3` in `LD_LIBRARY_PATH` with `miniconda3`
```bash
export LD_LIBRARY_PATH=${HOME}/anaconda3/envs/llm_mr_v2/lib/python3.11/site-packages/nvidia/nvjitlink/lib:${LD_LIBRARY_PATH}
export PYTHONPATH=$(pwd):${PYTHONPATH}
export OPENAI_API_KEY=Your OpenAI Key. You need to set it when you choose the infer type as OpenAI.
export OPENAI_API_BASE=Your OpenAI base url
export GOOGLE_API_KEY=Your Google Cloud key. you need to set it when you choose the infer type as Google.
export SERP_API_KEY= Get SERP API key from https://serpapi.com
```

We provide both English and Chinese version of prompt. Default version is English. If you wish to use Chinese version, please set this env:
``` bash
export PROMPT_LANGUAGE="zh"
```

## Model Set
⚠️ We strongly recommend using the Gemini Flash models. There may be unknown errors when using any other models. This project has high requirements for API consumption and concurrent volume, so it's not recommended to use locally deployed models.

The models used in the generation process are configured in the `./LLMxMapReduce_V2/config/model_config.json` file. Currently, we support both the OpenAI API and the Google API. You can specify the API to be used in the `infer_type` key. Additionally, you need to specify the model name in the `model` key.

Moreover, the crawling process also requires large language model (LLM) inference. You can make changes in a similar manner in the `./LLMxMapReduce_V2/src/start_pipeline.py` file. 

## Start LLMxMapReduce_V2 pipeline
Follow the instructions and generate a report. The generated Markdown file is at ./output/md. 
```bash
cd LLMxMapReduce_V2
bash scripts/pipeline_start.sh TOPIC output_file_path.jsonl
```

If you wish to use your own data, you need to set the `--input_file` and don't set `--topic` in scripts.

The input data should have following components at least:
```json
{
  "title": "The article title you wish to write",
  "papers": [
    {
      "title": "The material title",
      "abstract": "The abstract material. Optional, if not, part of the full text will be excerpted",
      "txt": "The reference material full content"
    }
  ]
}
```

You could use to use [this script](LLMxMapReduce_V2/scripts/output_to_md.py) to convert data from `.jsonl` to multiple `.md` files.

# 📃 Evaluation
The following steps are about LLMxMapReduce-V2.

Follow the steps below to set up the evaluation:
## 1. Download the Dataset
Before running the evaluation, you need to download the `test` split of [SurveyEval dataset](https://huggingface.co/datasets/R0k1e/SurveyEval). After downloading, store it in a `.jsonl` file.

## 2. Run the Evaluation
Execute the [scripts](LLMxMapReduce_V2/scripts/eval_all.sh) to evaluate the generated result. 
```bash
cd LLMxMapReduce_V2
bash scripts/eval_all.sh output_data_file_path.jsonl
```
Aware that the evaluation process is token-consuming, you need to make sure you have enough balance.

# 📊 Experiment Results
Our experiments demonstrate the improved performance of LLM using the LLMxMapReduce-V2 framework on SurveyEval. Detailed results are provided below.

| **Methods**           | **Struct.** | **Fait.** | **Rele.** | **Lang.** | **Crit.** | **Num.** | **Dens.** | **Prec.** | **Recall** |
|-----------------------|-------------|-----------|-----------|-----------|-----------|----------|-----------|-----------|------------|
| Vanilla               | 94.44       | 96.43     | **100.00**| **96.50** | 37.11     | 78.75    | **74.64** | 25.48     | 26.46      |
| + Skeleton            | **98.95**   | **97.03** | **100.00**| 95.95     | **41.01** | **135.15**| 72.96     | **62.60** | **65.11**  |
| AutoSurvey            | 86.00       | 93.10     | **100.00**| 92.90     | 68.39     | 423.35   | 31.97     | 50.12     | 51.73      |
| LLMxMapReduce_V2       | **95.00**   | **97.22** | **100.00**| **94.34** | **71.99** | **474.90**| **52.23** | **95.50** | **95.80**  |

# 📝 Citation
If you have used the content of this repository, please cite the paper and leave your star :).

```
@misc{wang2025llmtimesmapreducev2entropydrivenconvolutionaltesttime,
      title={LLM$\times$MapReduce-V2: Entropy-Driven Convolutional Test-Time Scaling for Generating Long-Form Articles from Extremely Long Resources}, 
      author={Haoyu Wang and Yujia Fu and Zhu Zhang and Shuo Wang and Zirui Ren and Xiaorong Wang and Zhili Li and Chaoqun He and Bo An and Zhiyuan Liu and Maosong Sun},
      year={2025},
      eprint={2504.05732},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2504.05732}, 
}

@misc{zhou2024llmtimesmapreducesimplifiedlongsequenceprocessing,
      title={LLM$\times$MapReduce: Simplified Long-Sequence Processing using Large Language Models}, 
      author={Zihan Zhou and Chong Li and Xinyi Chen and Shuo Wang and Yu Chao and Zhili Li and Haoyu Wang and Rongqiao An and Qi Shi and Zhixing Tan and Xu Han and Xiaodong Shi and Zhiyuan Liu and Maosong Sun},
      year={2024},
      eprint={2410.09342},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2410.09342}, 
}
```



