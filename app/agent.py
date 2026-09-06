import sys
from pathlib import Path
import json
import time

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import pandas as pd
from app.reconcile import reconcile_bank_to_ledger, reconcile_bank_to_invoices
from app.tax_matcher import build_unified_ledger
from app.generate_report import generate_full_report

class FinanceControllerAgent:
    """
    Autonomous Finance Operations Agent (Track 04)
    Executes a deliberate observe-plan-act-verify loop across unlinked financial data streams.
    """
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.memory = {}
        self.logs = []

    def log(self, step: str, thought: str):
        entry = f"[{step}] 💭 AGENT THOUGHT: {thought}"
        self.logs.append(entry)
        print(entry)

    # --- Tool Definitions ---
    def tool_load_sources(self):
        self.log("PERCEPTION", "Ingesting batch files: bank statements, general ledger, and invoices.")
        self.memory['bank'] = pd.read_csv(self.data_dir / "bank_statement.csv")
        self.memory['ledger'] = pd.read_csv(self.data_dir / "internal_ledger.csv")
        self.memory['invoices'] = pd.read_csv(self.data_dir / "invoices.csv")
        return f"Loaded: Bank ({len(self.memory['bank'])}), Ledger ({len(self.memory['ledger'])}), Invoices ({len(self.memory['invoices'])})"

    def tool_reconcile_sources(self):
        self.log("ACTION", "Executing 2-way cross-source reconciliations with tolerance heuristics.")
        bl = reconcile_bank_to_ledger(self.memory['bank'], self.memory['ledger'])
        bi = reconcile_bank_to_invoices(self.memory['bank'], self.memory['invoices'])
        
        bl.to_csv(self.data_dir / "bank_ledger_results.csv", index=False)
        bi.to_csv(self.data_dir / "bank_invoice_results.csv", index=False)
        
        self.memory['bl_results'] = bl
        self.memory['bi_results'] = bi
        
        bl_matched = len(bl[bl['status'] == 'MATCHED'])
        bi_matched = len(bi[bi['status'] == 'MATCHED'])
        return f"Reconciled: Bank->Ledger ({bl_matched} confident pairs), Bank->Invoice ({bi_matched} confident pairs)"

    def tool_unify_and_classify(self):
        self.log("ACTION", "Unifying matching clusters into canonical entities and assigning tax lines.")
        canonical = build_unified_ledger(
            self.memory['bank'],
            self.memory['ledger'],
            self.memory['invoices'],
            self.memory['bl_results'],
            self.memory['bi_results']
        )
        canonical.to_csv(self.data_dir / "canonical_ledger.csv", index=False)
        self.memory['canonical'] = canonical
        return f"Canonical ledger compiled: {len(canonical)} unique financial entities."

    def tool_verify_and_audit(self, elapsed: float):
        self.log("VERIFICATION", "Running verification layer: validating cash balance and isolating exceptions.")
        generate_full_report(elapsed)
        return "Audit complete. Verified cash position and generated honest_exception_report.csv."

    # --- Agent Controller Loop ---
    def run(self):
        start_time = time.time()
        print("\n" + "=" * 65)
        print("   🤖 AI FINANCE CONTROLLER AGENT ACTIVATED")
        print("   Goal: Autonomous verification & finance-ops loop closure")
        print("=" * 65)

        # Plan & Execute step 1
        self.log("PLAN", "Step 1: Check inputs across data silos.")
        res1 = self.tool_load_sources()
        print(f"       Observation: {res1}\n")

        # Plan & Execute step 2
        self.log("PLAN", "Step 2: Bridge transactions across bank, GL journal, and invoice records.")
        res2 = self.tool_reconcile_sources()
        print(f"       Observation: {res2}\n")

        # Plan & Execute step 3
        self.log("PLAN", "Step 3: Construct canonical records and determine corporate tax lines.")
        res3 = self.tool_unify_and_classify()
        print(f"       Observation: {res3}\n")

        # Plan & Execute step 4
        self.log("PLAN", "Step 4: Self-verify balances, calculate net cash flow, and export exception logs.")
        elapsed = time.time() - start_time
        res4 = self.tool_verify_and_audit(elapsed)
        print(f"       Observation: {res4}\n")

        print("=" * 65)
        print("   🎯 LOOP CLOSED: Agent completed finance controller operations.")
        print("=" * 65 + "\n")

if __name__ == "__main__":
    agent = FinanceControllerAgent()
    agent.run()
