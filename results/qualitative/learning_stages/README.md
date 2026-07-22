# Full96 learning-stage qualitative artifacts

These 10 NPZ/CSV/metadata triplets support Appendix Figures 20–22. They follow
one fixed raw event (unit 1143, frame 107200608), one contact domain, and four
fixed GT units (2143, 1143, 720, and 1129) through five scheduled checkpoints
from each Full96 duration run. Inference is pinned to commit `808d7fa`; scoring
uses seed 0, at most 100 events per unit, and 200 spike-excluded backgrounds.

Each exporter recomputed all 10 committed per-unit SNR and d′ rows and required
maximum absolute error below `1e-6` before writing an artifact. The local
renderer additionally requires exact event/template identity, voltage agreement
within `1e-6` µV, the expected sample exposure, and aggregate d′ agreement with
the committed trajectory table.

| route | step | windows | export job | elapsed / node | checkpoint SHA-256 | NPZ SHA-256 |
|---|---:|---:|---:|---|---|---|
| om0 | 135 | 34.6k | `23281634` | 00:09:01 / `n202` | `9a29206746aec7645dfb0c6feddf0fa84fc0ff9708e76ff25fa6e381b6f8a806` | `1dd424a0f465d34fda780671a12648069c658cad375352aefca8764fcf820402` |
| om0 | 459 | 117.5k | `23281635` | 00:09:02 / `n203` | `84677244c7c7ce3b98b8411b994727946e6d945da8a4ba36694966c901b2c31d` | `e710d097db17dca254c53c59d863f70b7228b83860337c9e188e779085ac9f1d` |
| om0 | 1565 | 400.6k | `23281636` | 00:08:57 / `n69` | `456f68d1930160e00a40580e6474e0d5f6510ca4e37dd4ab2228f3d9aab0ba87` | `dde13b73a136e44612644f8ce67991b60927a962d925e714ee389547f38d39fd` |
| om0 | 61903 | 15.85M | `23281637` | 00:08:31 / `n202` | `1802490a9831d0cadf04d0775a20596c3b279a262b6308d6c383c748dd1757de` | `d9d4e0845215e77f70364c027b38d89725b6b29c53712d6f113686052334943a` |
| om0 | 210923 | 54.0M | `23281638` | 00:08:30 / `n203` | `f30ea1c379aecde0337bd9b168d2d6fafe93529e025ba5c3d7f8a3c0e4321506` | `ecf17a2f07bd4107297ca2973b32334bd93dca202fd78fa8be2fe93f088602fd` |
| om1 | 135 | 34.6k | `23281639` | 00:08:26 / `n69` | `2aad7a8281a4f6e0e983481d34912c049c1a5c1a720d99599cbd8a8b81291657` | `1ce7a9f03bb7adc412b50dfc53266f429cdbb7d727eaecc8f670f9b93505f3d8` |
| om1 | 459 | 117.5k | `23281688` | 00:09:54 / `n69` | `67e599839a38da86eb46f2e11a88869f88dafb992cd2ff3509004cda4e6ab232` | `098caa48cf337bb88b8d5152473f271314941b31255dceb87e0e1b62c19cf6f2` |
| om1 | 1565 | 400.6k | `23281641` | 00:08:22 / `n69` | `35539113812b1787bf38798f52daba13584224c7634a1b4f4ad3ab6ab91e85dd` | `0d9ef59025148b49330512aae72eacf4fc20c7db5a33a666f5491e6bfcc685f0` |
| om1 | 61903 | 15.85M | `23281642` | 00:08:57 / `n202` | `4d32a22a455a67c8ecb5c84b2ee5af1c450c8df5adc3622734d54760ceac214f` | `d83194d261cd9e964d81ad173c032896dd476c9cf3318112d3d555b5b8a030b6` |
| om1 | 210923 | 54.0M | `23281643` | 00:08:59 / `n203` | `90d816c54d5a599ff01d1b65666ca3524588391054d58c4146eb713c48a7b15a` | `56b7e76a9b51b4f5525c443a2cb6a3b869066389319f5f38568beb564a440628` |

Nodes `n69`, `n202`, and `n203` provide TITAN X (Pascal), GTX 1080 Ti, and
TITAN Xp GPUs, respectively. Original job `23281640` ran the om1 step-459 export
on an A100 (`n04`) but was rejected because its recomputed `snr_deep` differed
from the frozen endpoint by `0.0012331008911132812`, above the `1e-6` artifact
contract. Replacement job `23281688` used `n69` and passed without weakening the
validation tolerance.

Auxiliary file SHA-256 values are:

| file | CSV SHA-256 | metadata JSON SHA-256 |
|---|---|---|
| `ib_w96_om0_scale_s00000135_examples` | `748dc92e742e5ac46fea54dfdaba93053ab92a0dd25c831a5af3270b462cb884` | `33d62e34c4c3accd9cac48509c14d227e0894312d87c14b851a18690fdbb2967` |
| `ib_w96_om0_scale_s00000459_examples` | `22cf86bde6cfc1f3884dc1fbfac6c0a00f44c3d95bd8469f8a65e438365aa192` | `5b6edfbdb303ac4d59f2fae77f57bba2d60cd7f2ce680e75995f45179b2a8dd9` |
| `ib_w96_om0_scale_s00001565_examples` | `238324a275d943c8420da933eed39dc607da78c2fc484f2017a2bc88685ff397` | `05043f9bc2f4bf8181832e27f916e37510b0b06c211625da1308d2e26d6585c4` |
| `ib_w96_om0_scale_s00061903_examples` | `7b8b24904134b1b9d2439cb0ffcb97f54a8cb5e84d160b810d6511de0fbdac3f` | `3f761ae834b8fc6ed1ccf16ff81662c9ca7e78675502de26b32bb244f484157c` |
| `ib_w96_om0_scale_s00210923_examples` | `bd56af52dbdef59165a8cc4fbc87c07d7ff1171292cc94ad8809cf6a2889f18a` | `686b165efebbd262b963b0f146833a759a83e56fc7fb14e39917193586bccbce` |
| `ib_w96_om1_scale_s00000135_examples` | `6a6ef1b756cc2efdd2fdd118d3d1a82bb2774885ab64a042fcf63a58b19bf46e` | `2c51007525c5bfe894cb55ee843f17e282816c98bf3d66e572cd649380b2cf1c` |
| `ib_w96_om1_scale_s00000459_examples` | `91fa53d675c1ca1d1800f066f1ac5d794f28ef428a23fe5a890911123e8e348d` | `ca655bd1b19b1acd57ed2a2f0d91323d45b8d582e30d08b861cc2ad02b116f12` |
| `ib_w96_om1_scale_s00001565_examples` | `8b958f9e98347ba9d94584e2b35cd8dd75abedbcaaa6908d2208e7a6478cfc3c` | `16238f0b66a813e2a819c128f269f2010d56bca948daeba8f8cf3e1693383a77` |
| `ib_w96_om1_scale_s00061903_examples` | `6d1593b0464211043048921700525f1fc282b74111d6d6534f350580d068238b` | `3d7c9487b4ee6dd22a0d8ec66ac3e991c93d7040ac2cc3e58038628b6267b5eb` |
| `ib_w96_om1_scale_s00210923_examples` | `37eae2a7cf889a3d7615fd76c1c4e9d92228900051205728e186b3a75db0ad48` | `a43465ed5be38b58003dbf2511126ebb1556c0e97b7f45050e9e11fc4e1c1c20` |

Rendered figure SHA-256 values are:

| figure | SHA-256 |
|---|---|
| `learning_voltage_evolution.png` | `dce01b6a34018fd8cc4f76c199bbe1fe8bde0502057e3f2239f47b609d020fc2` |
| `learning_unit_profile_evolution_om0.png` | `34bb471912f7bd04f2f77325e3bb93ea37b3101afba5c232598f3dc6b59b82c8` |
| `learning_unit_profile_evolution_om1.png` | `ce4a7a5ce0226174c6259de91a11612d37df5d48b17c183af37614cb726708b0` |

Regenerate the figures locally from this directory with:

```bash
python code/figures/learning_evolution.py
```