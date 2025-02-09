import json
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Building, Activity, Organization

# Загружаем JSON-файл
with open("test_data.json", "r", encoding="utf-8") as file:
    data = json.load(file)


def insert_test_data():
    db: Session = SessionLocal()

    try:
        # Проверяем, есть ли уже данные в базе
        if db.query(Building).first() or db.query(Activity).first() or db.query(Organization).first():
            print("✅ База уже содержит тестовые данные. Пропускаем загрузку.")
            return

        print("ℹ️ Загружаем тестовые данные в базу...")

        # 1. Загружаем здания
        for b in data["buildings"]:
            building = Building(id=b["id"], address=b["address"], latitude=b["latitude"], longitude=b["longitude"])
            db.add(building)

        # 2. Загружаем виды деятельности
        for a in data["activities"]:
            activity = Activity(id=a["id"], name=a["name"], parent_id=a["parent_id"])
            db.add(activity)

        # 3. Загружаем организации и связываем их с видами деятельности
        for o in data["organizations"]:
            organization = Organization(
                id=o["id"],
                name=o["name"],
                phone_numbers=json.dumps(o["phone_numbers"]),  # Сохраняем как JSON-строку
                building_id=o["building_id"]
            )
            db.add(organization)
            db.flush()  # Обновляем объект в БД, чтобы получить его ID

            # Добавляем связи организация ↔ деятельность
            for activity_id in o["activity_ids"]:
                activity = db.query(Activity).filter(Activity.id == activity_id).first()
                if activity:
                    organization.activities.append(activity)

        db.commit()
        print("✅ Данные успешно загружены в базу!")

    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка при загрузке данных: {e}")

    finally:
        db.close()


# Запускаем загрузку данных
if __name__ == "__main__":
    insert_test_data()
