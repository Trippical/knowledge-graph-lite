---
title: Approval authority
entity: Approval Authority
type: POLICY
description: "Manual adjustment sign-off bands: up to £100 Support Lead; £100–£500 Ops Manager; over £500 VP Finance. Delegation goes one level up and must be recorded in the ops calendar."
aliases:
  - sign-off
  - approvals
  - escalation path
relations:
  - Manual Adjustment approved_by Support Lead
  - Manual Adjustment approved_by Ops Manager
  - Manual Adjustment approved_by VP Finance
  - Cap Override approved_by Campaign Owner
  - Cap Override approved_by VP Finance
  - Ops Manager delegates_to VP Finance
  - Clawback Dispute escalates_to Ops Manager
answers:
  - Who approves a manual reward adjustment?
  - Who signs off when the Ops Manager is away?
  - Who approves a cap override on a live campaign?
  - Who handles a customer dispute about a clawback?
updated: 2026-08-21
---

# Approval authority

## Who approves manual reward adjustments

- Up to £100: Support Lead.
- £100–£500: Ops Manager.
- Over £500: VP Finance.

## Who approves cap overrides

Cap overrides (RR-30) on a live campaign require the Campaign Owner and
the VP Finance together.

## Delegation when an approver is away

Authority delegates one level up, not down: if the Ops Manager is out,
their band goes to the VP Finance (per SCHEMA.md, "X delegates_to Y" =
when X is unavailable, X's authority passes to Y). Delegations are
recorded in the ops calendar; verbal delegation is not valid.

## Escalation for disputed reversals

Customer disputes a clawback (RR-20..22) → Support Lead reviews within
2 business days → unresolved cases go to the Ops Manager with the
clearing-file evidence attached.

## Name changes

- 2026-08-21: Finance Director renamed to VP Finance. Old name is an
  alias on [vp-finance.md](vp-finance.md).
