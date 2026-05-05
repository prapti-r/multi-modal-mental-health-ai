"""
Seed the therapist directory with initial data.

Emergency contacts (is_emergency_contact=True) appear at the top of the
Severe Risk / Crisis screen

"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Allow running from backend/ root
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from models.therapist import Therapist

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


#  Seed data 

#  EMERGENCY / CRISIS LINES 
THERAPIST_SEED: list[dict] = [
    {
        "name":                 "iCall – Vandrevala Foundation Helpline",
        "specialization":       "24/7 Mental Health Crisis Line",
        "contact_number":       "1860-2662-345",
        "location":             "Nationwide (India)",
        "is_emergency_contact": True,
    },
    {
        "name":                 "Vandrevala Foundation WhatsApp Support",
        "specialization":       "24/7 Crisis Chat & Counselling",
        "contact_number":       "+91-9999-666-555",
        "location":             "Nationwide (India)",
        "is_emergency_contact": True,
    },
    {
        "name":                 "Snehi Mental Health Helpline",
        "specialization":       "Emotional Support & Suicide Prevention",
        "contact_number":       "+91-44-24640050",
        "location":             "Nationwide (India)",
        "is_emergency_contact": True,
    },

    #  CLINICAL PSYCHOLOGISTS 
    {
        "name":                 "Dr. Priya Sharma",
        "specialization":       "Clinical Psychologist – Anxiety & Depression",
        "contact_number":       "+977-1-4412345",
        "location":             "Kathmandu, Nepal",
        "is_emergency_contact": False,
    },
    {
        "name":                 "Dr. Anita Maharjan",
        "specialization":       "Clinical Psychologist – Trauma & PTSD",
        "contact_number":       "+977-1-4423456",
        "location":             "Patan, Nepal",
        "is_emergency_contact": False,
    },
    {
        "name":                 "Dr. Rohan Karki",
        "specialization":       "Clinical Psychologist – Adolescent Mental Health",
        "contact_number":       "+977-1-4434567",
        "location":             "Kathmandu, Nepal",
        "is_emergency_contact": False,
    },

    #  CBT SPECIALISTS 
    {
        "name":                 "Ms. Sunita Thapa",
        "specialization":       "CBT Specialist – Stress & Burnout",
        "contact_number":       "+977-1-4445678",
        "location":             "Lalitpur, Nepal",
        "is_emergency_contact": False,
    },
    {
        "name":                 "Mr. Bikash Shrestha",
        "specialization":       "CBT Specialist – OCD & Panic Disorder",
        "contact_number":       "+977-1-4456789",
        "location":             "Kathmandu, Nepal",
        "is_emergency_contact": False,
    },
    {
        "name":                 "Ms. Asmita Rai",
        "specialization":       "CBT Specialist – Depression & Low Mood",
        "contact_number":       "+977-1-4467890",
        "location":             "Online",
        "is_emergency_contact": False,
    },

    #  PSYCHIATRISTS 
    {
        "name":                 "Dr. Suresh Adhikari",
        "specialization":       "Psychiatrist – Mood Disorders & Medication",
        "contact_number":       "+977-1-4478901",
        "location":             "Kathmandu, Nepal",
        "is_emergency_contact": False,
    },
    {
        "name":                 "Dr. Mina Gurung",
        "specialization":       "Psychiatrist – Anxiety & Bipolar Disorder",
        "contact_number":       "+977-1-4489012",
        "location":             "Bhaktapur, Nepal",
        "is_emergency_contact": False,
    },

    #  ONLINE / TELEHEALTH 
    {
        "name":                 "Mindbloom Telehealth",
        "specialization":       "Online Counselling – General Mental Health",
        "contact_number":       "+977-1-4490123",
        "location":             "Online",
        "is_emergency_contact": False,
    },
    {
        "name":                 "The Mind Clinic – Online",
        "specialization":       "Online Therapy – Young Adults & Students",
        "contact_number":       "+977-980-1234567",
        "location":             "Online",
        "is_emergency_contact": False,
    },
]


#  Seeder 

async def seed(clear: bool = False) -> None:
    async with AsyncSessionLocal() as db:
        async with db.begin():
            if clear:
                await db.execute(delete(Therapist))
                logger.info("Existing therapist rows cleared.")

            rows = [Therapist(**data) for data in THERAPIST_SEED]
            db.add_all(rows)

        logger.info(
            f"Seeded {len(rows)} therapist records "
            f"({sum(1 for r in rows if r.is_emergency_contact)} emergency contacts)."
        )

        # Log summary
        emergency = [r for r in rows if r.is_emergency_contact]
        regular = [r for r in rows if not r.is_emergency_contact]

        logger.info("\n── Emergency Contacts ")
        for r in emergency:
            logger.info(f"  ✓ {r.name}  |  {r.contact_number}")

        logger.info("\n── Regular Directory ")
        for r in regular:
            logger.info(f"  · {r.name}  ({r.specialization})  |  {r.location}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed therapist directory.")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Delete all existing therapist rows before seeding.",
    )
    args = parser.parse_args()
    asyncio.run(seed(clear=args.clear))