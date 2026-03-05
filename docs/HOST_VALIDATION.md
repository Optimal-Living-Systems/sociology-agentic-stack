# Host Validation Report

**Date:** 2026-03-05T00:45:28-05:00
**Machine:** joel-coding-01
**Purpose:** Primary build host for OLS Agentic Sociology Research Stack

## System Info
```
Linux joel-coding-01 6.17.0-14-generic #14~24.04.1-Ubuntu SMP PREEMPT_DYNAMIC Thu Jan 15 15:52:10 UTC 2 x86_64 x86_64 x86_64 GNU/Linux
```

## OS
```
Distributor ID:	Ubuntu
Description:	Ubuntu 24.04.4 LTS
Release:	24.04
Codename:	noble
```

## Python
```
Python 3.12.3
pip 24.0 from /usr/lib/python3/dist-packages/pip (python 3.12)
```

## Docker
```
Docker version 29.2.1, build a5c7197
Docker Compose version v5.0.2
```

## GPU
```
Failed to initialize NVML: Unknown Error
NVML ERROR — GPU driver issue, not a blocker for MVP-A
```

## Running Containers
```
Docker not running
```

## Memory
```
               total        used        free      shared  buff/cache   available
Mem:           125Gi        11Gi       104Gi       4.9Gi        14Gi       114Gi
Swap:          8.0Gi          0B       8.0Gi
```

## Storage
```
Filesystem      Size  Used Avail Use% Mounted on
/dev/nvme0n1p3  155G  140G  7.2G  96% /home
```

## CPU
```
Architecture:                            x86_64
CPU op-mode(s):                          32-bit, 64-bit
Address sizes:                           48 bits physical, 48 bits virtual
Byte Order:                              Little Endian
CPU(s):                                  32
On-line CPU(s) list:                     0-31
Vendor ID:                               AuthenticAMD
Model name:                              AMD Ryzen 9 5900XT 16-Core Processor
CPU family:                              25
Model:                                   33
Thread(s) per core:                      2
Core(s) per socket:                      16
Socket(s):                               1
Stepping:                                2
Frequency boost:                         enabled
CPU(s) scaling MHz:                      63%
CPU max MHz:                             4981.5098
CPU min MHz:                             570.1730
BogoMIPS:                                6600.41
Flags:                                   fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ht syscall nx mmxext fxsr_opt pdpe1gb rdtscp lm constant_tsc rep_good nopl xtopology nonstop_tsc cpuid extd_apicid aperfmperf rapl pni pclmulqdq monitor ssse3 fma cx16 sse4_1 sse4_2 x2apic movbe popcnt aes xsave avx f16c rdrand lahf_lm cmp_legacy svm extapic cr8_legacy abm sse4a misalignsse 3dnowprefetch osvw ibs skinit wdt tce topoext perfctr_core perfctr_nb bpext perfctr_llc mwaitx cpb cat_l3 cdp_l3 hw_pstate ssbd mba ibrs ibpb stibp vmmcall fsgsbase bmi1 avx2 smep bmi2 erms invpcid cqm rdt_a rdseed adx smap clflushopt clwb sha_ni xsaveopt xsavec xgetbv1 xsaves cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local user_shstk clzero irperf xsaveerptr rdpru wbnoinvd arat npt lbrv svm_lock nrip_save tsc_scale vmcb_clean flushbyasid decodeassists pausefilter pfthreshold avic v_vmsave_vmload vgif v_spec_ctrl umip pku ospke vaes vpclmulqdq rdpid overflow_recov succor smca fsrm debug_swap
```

## /proc/meminfo (top 5)
```
MemTotal:       131820840 kB
MemFree:        109267436 kB
MemAvailable:   119730392 kB
Buffers:          317332 kB
Cached:         14239780 kB
```

## Existing Tools
- Ollama:
```
/home/joel/.local/bin/ollama
Warning: could not connect to a running Ollama instance
Warning: client version is 0.17.5
```
- Kestra:
```
Kestra CLI not found (OK if running in Docker)
```
- Git:
```
git version 2.43.0
```

## Validation Status
- [x] Ubuntu 24.04 confirmed
- [x] Python 3.12+ confirmed
- [x] Docker + Compose confirmed
- [ ] GPU accessible (or noted as non-blocker)
- [x] Sufficient RAM (128GB target)
- [x] Sufficient storage

## Python Dependencies
```
sherpa-ai OK
/home/joel/work/sociology-agentic-stack/.venv/lib/python3.12/site-packages/requests/__init__.py:113: RequestsDependencyWarning: urllib3 (2.6.3) or chardet (7.0.1)/charset_normalizer (3.4.4) doesn't match a supported version!
  warnings.warn(
langfuse OK
/home/joel/work/sociology-agentic-stack/.venv/lib/python3.12/site-packages/requests/__init__.py:113: RequestsDependencyWarning: urllib3 (2.6.3) or chardet (7.0.1)/charset_normalizer (3.4.4) doesn't match a supported version!
  warnings.warn(
instructor OK
lancedb OK
pydantic OK
jsonschema OK
PyYAML OK
python-dotenv OK
httpx OK
tenacity OK
```

## Python Dependencies (After Compatibility Pin)
```
sherpa-ai OK
langfuse OK
instructor OK
lancedb OK
pydantic OK
jsonschema OK
PyYAML OK
python-dotenv OK
httpx OK
tenacity OK
```
