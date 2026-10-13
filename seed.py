from datetime import date, timedelta

from main import Member, PLAN_MONTHS, SessionLocal, add_months

db = SessionLocal()

if db.query(Member).count() > 0:
    print("Members already exist - nothing to do.")
    print("To start fresh: stop the server, delete gym.db, run this file again.")
    raise SystemExit

today = date.today()


def member(code, name, email, phone, plan, trainer, days_until_end, billing="PAID", frozen=False):
    """Dates are worked out from today, so the sample data always makes sense."""
    end = today + timedelta(days=days_until_end)
    # start = one cycle before the end date
    start = add_months(end, -PLAN_MONTHS[plan])
    return Member(
        member_code=code, name=name, email=email, phone=phone, plan=plan,
        trainer=trainer, start_date=start, end_date=end, billing=billing, frozen=frozen,
    )


db.add_all([
    member("ITK-1024", "Arjun Kumar",    "arjun.kumar@domain.in",    "+91 98765 43221", "Premium",  "Rohan Mehta", 103),
    member("ITK-1025", "Priya Sharma",   "priya.s@techcorp.io",      "+91 98112 34567", "Standard", "Meena Iyer",   60),
    member("ITK-1026", "Vikram Reddy",   "vikram.reddy@apex.org",    "+91 97234 56789", "Premium",  "Rohan Mehta",   3),
    member("ITK-1027", "Ananya Patel",   "ananya.p@designlab.co",    "+91 96543 21987", "Basic",    "Sanjay Pillai", 75, billing="PENDING"),
    member("ITK-1028", "Rahul Verma",    "rahul.verma@corp.net",     "+91 95432 10987", "Standard", "Meena Iyer",   -30),
    member("ITK-1029", "Devendra Singh", "devendra.singh@mail.in",   "+91 94321 09876", "Premium",  "Sanjay Pillai", 150, frozen=True),
])
db.commit()
print("Added 6 sample members.")
