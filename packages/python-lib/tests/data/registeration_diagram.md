# State Graph Diagram: Registration

Generated from: `registeration.yaml`

## Statistics
- **Nodes**: 23 PropertyInstances
- **Edges**: 28 ConstraintInstances
  - Structural edges: 13
  - X-sup edges: 15

## Diagram

```mermaid
graph TD
    126901cc_cffe_401f_9476_e7c62d708146["Registration.id"]
    a297b345_aa56_4de6_bf7a_83fcc817d4d5["Registration.registrant.id"]
    12507c3f_3445_4f10_ab94_a9cb8dc50845["Registration.registrant.name"]
    ef5e18fe_1a00_4adc_abf5_4b477a229219["Registration.registrant.email"]
    d2943aee_7cc1_4969_bf97_8e448fe2e084["Registration.registrant"]
    e349543b_5b66_45ab_b7d4_366473b594cc["Registration.event.id"]
    abf73f09_1cdd_43c3_ae44_5409c058d36d["Registration.event.name"]
    9cac9e13_ca61_4846_947e_ccf16704f58f["Registration.event.description"]
    474604e4_60a9_484a_a5f3_937e2ec07f34["Registration.event.schedule"]
    23484081_674c_4b7e_920e_de962fd4f61a["Registration.event.capacity"]
    9c4c6d6b_f4e4_4836_bf68_003b33ae8022["Registration.event.remaining"]
    57d94e41_c499_4968_9a82_94af783e8b43["Registration.event.pricing"]
    1cdbe1b3_e612_461d_b0d9_3f5f2b3415a6["Registration.event"]
    e61eb9aa_30b8_44c0_9a18_c786b545f0fc["Registration.guests"]
    2859ecc9_8c20_4170_ab3c_aa9aa0b793e5["Registration.guests[*].id"]
    a57b7bc8_3299_4481_93e8_785226326444["Registration.guests[*].name"]
    c36ab647_7b2c_4de5_a10b_f5d614b2ddf0["Registration.guests[*].email"]
    b3f98787_abe7_4e34_8382_debff985f52a["Registration.guests[*].invitation.subject"]
    bff42841_62a0_41f3_8879_28078e3f0cbb["Registration.guests[*].invitation.body"]
    8ca75cb7_07bb_4868_91a3_f8a587ec064f["Registration.guests[*].invitation.send_at"]
    490f7f61_301e_4880_870a_19361f47d1dc["Registration.guests[*].invitation"]
    743bdb90_28bc_4c04_92b6_6a6bd0390d4b["Registration.total_price"]
    b696f0ea_abea_4e34_88d6_eced7f7e7d13["Registration.status"]
    d2943aee_7cc1_4969_bf97_8e448fe2e084 -->|structural| a297b345_aa56_4de6_bf7a_83fcc817d4d5
    d2943aee_7cc1_4969_bf97_8e448fe2e084 -->|structural| 12507c3f_3445_4f10_ab94_a9cb8dc50845
    d2943aee_7cc1_4969_bf97_8e448fe2e084 -->|structural| ef5e18fe_1a00_4adc_abf5_4b477a229219
    1cdbe1b3_e612_461d_b0d9_3f5f2b3415a6 -->|structural| e349543b_5b66_45ab_b7d4_366473b594cc
    1cdbe1b3_e612_461d_b0d9_3f5f2b3415a6 -->|structural| abf73f09_1cdd_43c3_ae44_5409c058d36d
    1cdbe1b3_e612_461d_b0d9_3f5f2b3415a6 -->|structural| 9cac9e13_ca61_4846_947e_ccf16704f58f
    1cdbe1b3_e612_461d_b0d9_3f5f2b3415a6 -->|structural| 474604e4_60a9_484a_a5f3_937e2ec07f34
    1cdbe1b3_e612_461d_b0d9_3f5f2b3415a6 -->|structural| 23484081_674c_4b7e_920e_de962fd4f61a
    1cdbe1b3_e612_461d_b0d9_3f5f2b3415a6 -->|structural| 9c4c6d6b_f4e4_4836_bf68_003b33ae8022
    1cdbe1b3_e612_461d_b0d9_3f5f2b3415a6 -->|structural| 57d94e41_c499_4968_9a82_94af783e8b43
    d2943aee_7cc1_4969_bf97_8e448fe2e084 -->|xsup:validated| 1cdbe1b3_e612_461d_b0d9_3f5f2b3415a6
    1cdbe1b3_e612_461d_b0d9_3f5f2b3415a6 -->|xsup:edited| 2859ecc9_8c20_4170_ab3c_aa9aa0b793e5
    d2943aee_7cc1_4969_bf97_8e448fe2e084 -->|xsup:validated| 2859ecc9_8c20_4170_ab3c_aa9aa0b793e5
    1cdbe1b3_e612_461d_b0d9_3f5f2b3415a6 -->|xsup:edited| a57b7bc8_3299_4481_93e8_785226326444
    d2943aee_7cc1_4969_bf97_8e448fe2e084 -->|xsup:validated| a57b7bc8_3299_4481_93e8_785226326444
    1cdbe1b3_e612_461d_b0d9_3f5f2b3415a6 -->|xsup:edited| c36ab647_7b2c_4de5_a10b_f5d614b2ddf0
    d2943aee_7cc1_4969_bf97_8e448fe2e084 -->|xsup:validated| c36ab647_7b2c_4de5_a10b_f5d614b2ddf0
    490f7f61_301e_4880_870a_19361f47d1dc -->|structural| b3f98787_abe7_4e34_8382_debff985f52a
    1cdbe1b3_e612_461d_b0d9_3f5f2b3415a6 -->|xsup:edited| b3f98787_abe7_4e34_8382_debff985f52a
    d2943aee_7cc1_4969_bf97_8e448fe2e084 -->|xsup:validated| b3f98787_abe7_4e34_8382_debff985f52a
    490f7f61_301e_4880_870a_19361f47d1dc -->|structural| bff42841_62a0_41f3_8879_28078e3f0cbb
    1cdbe1b3_e612_461d_b0d9_3f5f2b3415a6 -->|xsup:edited| bff42841_62a0_41f3_8879_28078e3f0cbb
    d2943aee_7cc1_4969_bf97_8e448fe2e084 -->|xsup:validated| bff42841_62a0_41f3_8879_28078e3f0cbb
    490f7f61_301e_4880_870a_19361f47d1dc -->|structural| 8ca75cb7_07bb_4868_91a3_f8a587ec064f
    1cdbe1b3_e612_461d_b0d9_3f5f2b3415a6 -->|xsup:edited| 8ca75cb7_07bb_4868_91a3_f8a587ec064f
    d2943aee_7cc1_4969_bf97_8e448fe2e084 -->|xsup:validated| 8ca75cb7_07bb_4868_91a3_f8a587ec064f
    1cdbe1b3_e612_461d_b0d9_3f5f2b3415a6 -->|xsup:edited| 490f7f61_301e_4880_870a_19361f47d1dc
    d2943aee_7cc1_4969_bf97_8e448fe2e084 -->|xsup:validated| 490f7f61_301e_4880_870a_19361f47d1dc
```

## Legend

- **Structural edges**: Parent → Child property relationships (auto-generated)
- **X-sup edges**: Explicit constraint dependencies from x-sup extensions
- **Node labels**: Property IDs (e.g., `Registration.event.name`)

## Notes

This diagram shows the dependency graph where:
- Each node is a PropertyInstance with a unique UUID
- Edges represent ConstraintInstances (dependencies)
- Arrow direction: prerequisite → dependent
