"""
wisdom_payment.py - Unified Ledger Payment Layer
1 Credit = 1 USD | Min cashout: $50 | Platform fee: 18%
"""
import os, re, uuid, hashlib
from datetime import datetime
from neo4j import GraphDatabase

def strip_emoji(text):
    if not isinstance(text, str): return str(text) if text else ""
    p = re.compile("["+u"\U0001F600-\U0001F64F"+u"\U0001F300-\U0001F5FF"+
        u"\U0001F680-\U0001F6FF"+u"\U0001F1E0-\U0001F1FF"+
        u"\U00002600-\U000027BF"+u"\U0001F900-\U0001F9FF"+"]+",flags=re.UNICODE)
    return p.sub("", text).strip()

NEO4J_URI  = os.environ.get("NEO4J_URI",  "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASS = os.environ.get("NEO4J_PASS", "password123")
MIN_CASHOUT_USD = 50.0
PLATFORM_FEE    = 0.18
AFFILIATE_RATE  = 0.20
class WisdomLedger:
    def __init__(self):
        try:
            self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
            print("WisdomLedger: Connected to Neo4j")
        except Exception as e:
            print(f"Connection failed: {e}")
            self.driver = None

    def close(self):
        if self.driver: self.driver.close()

    def create_user(self, user_id, email, name, referred_by_code=None):
        email = strip_emoji(email); name = strip_emoji(name)
        aff_code = hashlib.md5(f"{user_id}{email}".encode()).hexdigest()[:8].upper()
        now = datetime.now().isoformat()
        try:
            with self.driver.session() as session:
                session.run("""
                    MERGE (u:User {id: $id})
                    SET u.email=$email, u.name=$name,
                        u.affiliate_code=$aff_code,
                        u.credit_balance=0.0,
                        u.total_earned=0.0,
                        u.total_spent=0.0,
                        u.total_withdrawn=0.0,
                        u.created_at=$now, u.updated_at=$now
                """, id=user_id, email=email, name=name, aff_code=aff_code, now=now)
                if referred_by_code:
                    session.run("""
                        MATCH (r:User {affiliate_code: $code})
                        MATCH (u:User {id: $uid})
                        MERGE (u)-[:REFERRED_BY]->(r)
                    """, code=referred_by_code.upper(), uid=user_id)
            print(f"User created: {user_id} | Code: {aff_code}")
            return {"user_id": user_id, "affiliate_code": aff_code}
        except Exception as e:
            print(f"create_user ERROR: {e}"); return {}

    def get_balance(self, user_id):
        try:
            with self.driver.session() as session:
                r = session.run(
                    "MATCH (u:User {id:$id}) RETURN u.credit_balance AS b",
                    id=user_id).single()
                return float(r["b"]) if r else 0.0
        except Exception as e:
            print(f"get_balance ERROR: {e}"); return 0.0

    def add_credit(self, user_id, amount, reason, ref_id=None):
        reason = strip_emoji(reason)
        tx_id = str(uuid.uuid4())[:12]; now = datetime.now().isoformat()
        try:
            with self.driver.session() as session:
                session.run("""
                    CREATE (t:Transaction {id:$tx_id, amount:$amount,
                        type:'credit_in', reason:$reason,
                        ref_id:$ref_id, status:'completed', created_at:$now})
                """, tx_id=tx_id, amount=amount, reason=reason,
                     ref_id=ref_id or "", now=now)
                session.run("""
                    MATCH (u:User {id:$uid})
                    SET u.credit_balance=u.credit_balance+$amount,
                        u.total_earned=u.total_earned+$amount,
                        u.updated_at=$now
                    WITH u MATCH (t:Transaction {id:$tx_id})
                    MERGE (u)-[:EARNED_FROM]->(t)
                """, uid=user_id, amount=amount, tx_id=tx_id, now=now)
            print(f"Credit added: +${amount} -> {user_id} ({reason})")
            return {"tx_id": tx_id, "amount": amount}
        except Exception as e:
            print(f"add_credit ERROR: {e}"); return {}

    def spend_credit(self, user_id, amount, reason, ref_id=None):
        reason = strip_emoji(reason)
        balance = self.get_balance(user_id)
        if balance < amount:
            return {"error": "insufficient_balance", "balance": balance}
        tx_id = str(uuid.uuid4())[:12]; now = datetime.now().isoformat()
        try:
            with self.driver.session() as session:
                session.run("""
                    CREATE (t:Transaction {id:$tx_id, amount:$amount,
                        type:'spend', reason:$reason,
                        ref_id:$ref_id, status:'completed', created_at:$now})
                """, tx_id=tx_id, amount=amount, reason=reason,
                     ref_id=ref_id or "", now=now)
                session.run("""
                    MATCH (u:User {id:$uid})
                    SET u.credit_balance=u.credit_balance-$amount,
                        u.total_spent=u.total_spent+$amount,
                        u.updated_at=$now
                    WITH u MATCH (t:Transaction {id:$tx_id})
                    MERGE (u)-[:SPENT_ON]->(t)
                """, uid=user_id, amount=amount, tx_id=tx_id, now=now)
            print(f"Credit spent: -${amount} from {user_id} ({reason})")
            return {"tx_id": tx_id, "amount": amount}
        except Exception as e:
            print(f"spend_credit ERROR: {e}"); return {}

    def process_affiliate_commission(self, new_user_id, subscription_amount):
        try:
            with self.driver.session() as session:
                r = session.run("""
                    MATCH (u:User {id:$uid})-[:REFERRED_BY]->(ref:User)
                    RETURN ref.id AS rid
                """, uid=new_user_id).single()
            if not r: return {"message": "No referrer found"}
            commission = round(subscription_amount * AFFILIATE_RATE, 2)
            self.add_credit(r["rid"], commission, "affiliate_commission", new_user_id)
            print(f"Affiliate: ${commission} -> {r['rid']}")
            return {"referrer_id": r["rid"], "commission": commission}
        except Exception as e:
            print(f"affiliate ERROR: {e}"); return {}

    def process_blueprint_sale(self, buyer_id, seller_id, blueprint_id, price):
        platform_cut = round(price * PLATFORM_FEE, 2)
        seller_cut = round(price - platform_cut, 2)
        result = self.spend_credit(buyer_id, price, "blueprint_purchase", blueprint_id)
        if "error" in result: return result
        self.add_credit(seller_id, seller_cut, "blueprint_sale", blueprint_id)
        try:
            with self.driver.session() as session:
                session.run("""
                    MATCH (u:User {id:$bid})
                    MATCH (b:Blueprint {id:$bpid})
                    MERGE (u)-[:PURCHASED]->(b)
                    SET b.downloads=coalesce(b.downloads,0)+1
                """, bid=buyer_id, bpid=blueprint_id)
        except Exception as e:
            print(f"Blueprint link ERROR: {e}")
        print(f"Sale: ${price} | Seller:+${seller_cut} | Platform:+${platform_cut}")
        return {"price": price, "seller_cut": seller_cut, "platform_cut": platform_cut}

    def request_payout(self, user_id, amount, method, bank_info=None):
        method = strip_emoji(method)
        balance = self.get_balance(user_id)
        if balance < MIN_CASHOUT_USD:
            return {"error": "below_minimum",
                    "message": f"Can ${MIN_CASHOUT_USD} de rut. Hien tai: ${balance}"}
        if amount > balance:
            return {"error": "insufficient_balance",
                    "message": f"So du: ${balance}"}
        w_id = str(uuid.uuid4())[:12]; now = datetime.now().isoformat()
        try:
            with self.driver.session() as session:
                session.run("""
                    CREATE (w:Withdrawal {id:$wid, amount:$amount,
                        method:$method, status:'pending',
                        bank_info:$bi, created_at:$now, processed_at:null})
                """, wid=w_id, amount=amount, method=method,
                     bi=str(bank_info or {}), now=now)
                session.run("""
                    MATCH (u:User {id:$uid})
                    SET u.credit_balance=u.credit_balance-$amount,
                        u.total_withdrawn=u.total_withdrawn+$amount,
                        u.updated_at=$now
                    WITH u MATCH (w:Withdrawal {id:$wid})
                    MERGE (u)-[:REQUESTED_PAYOUT]->(w)
                """, uid=user_id, amount=amount, wid=w_id, now=now)
            print(f"Payout: ${amount} via {method} by {user_id}")
            return {"withdrawal_id": w_id, "amount": amount,
                    "method": method, "status": "pending"}
        except Exception as e:
            print(f"request_payout ERROR: {e}"); return {"error": str(e)}

    def get_user_summary(self, user_id):
        try:
            with self.driver.session() as session:
                r = session.run("""
                    MATCH (u:User {id:$id})
                    RETURN u.credit_balance AS balance,
                           u.total_earned AS earned,
                           u.total_spent AS spent,
                           u.total_withdrawn AS withdrawn,
                           u.affiliate_code AS code
                """, id=user_id).single()
                return dict(r) if r else {"error": "not_found"}
        except Exception as e:
            print(f"summary ERROR: {e}"); return {}


if __name__ == "__main__":
    ledger = WisdomLedger()
    print("\n--- Test create users ---")
    r = ledger.create_user("user_001", "alice@test.com", "Alice")
    print(r)
    ledger.create_user("user_002", "bob@test.com", "Bob",
                       referred_by_code=r.get("affiliate_code", ""))
    print("\n--- Test affiliate commission ---")
    ledger.process_affiliate_commission("user_002", 199.0)
    print("\n--- Balance Alice ---")
    print(f"${ledger.get_balance('user_001')}")
    print("\n--- Test payout (should fail - below minimum) ---")
    print(ledger.request_payout("user_001", 30.0, "bank_transfer"))
    print("\n--- Summary ---")
    print(ledger.get_user_summary("user_001"))
    ledger.close()