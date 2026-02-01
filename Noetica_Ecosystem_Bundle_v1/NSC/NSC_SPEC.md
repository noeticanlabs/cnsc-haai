# NSC (Noetic Compiler) — Canonical Spec v1.0

## 1) Packet format
```yaml
NSC_Packet:
  header:
    version: 6.1
    author: Noetica Project
    mode: symbolic|math|exec
  body:
    content: "φ⊕↻∆◯⊖φ"
  footer:
    hash: coherence_crc32
```

Canonicalization rules:
- UTF-8
- LF line endings
- stable key ordering
- strip trailing whitespace

## 2) Grammar (Phase-1 EBNF)
```ebnf
program   = sentence , { ";" , sentence } ;
sentence  = phrase , [ "⇒" , phrase ] ;
phrase    = { atom | group } ;
group     = "[" , phrase , "]" | "(" , phrase , ")" ;
atom      = "φ" | "↻" | "⊕" | "⊖" | "◯" | "□" | "∆" | "↺" | "⇐" | "⇒" ;
```

## 3) Bytecode (Phase-1)
| Opcode | Glyph | Meaning |
|---:|:---:|---|
| 0x01 | φ | load θ |
| 0x02 | ↻ | curvature coupling |
| 0x03 | ⊕ | source +s |
| 0x04 | ⊖ | sink −s |
| 0x05 | ◯ | ∇²θ |
| 0x06 | ∆ | close EOM |
| 0x07 | ⇒ | time marker |
| 0x08 | □ | boundary |

## 4) VM state
pc, stack, env, receipt_sink (deterministic stepping)

## 5) Execution target
Emits PDE template shape:
E[θ] := ∂tθ − α∇²θ + γ∂tθ + βRθ − s = 0

## 6) Receipts
Each step includes: pc before/after, opcode, span, env hash, emitted object, chained run hash.
