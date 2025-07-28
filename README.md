#ALX-PROJECT-NEXUS
## e-commerce

A **production-ready, enterprise-grade e-commerce backend API** built with Django REST Framework.

---

## 🚀 Overview

e-commerce is a robust and scalable RESTful API for modern e-commerce platforms, providing secure user authentication, product management, order processing, and seamless payment integration.

---

## ✨ Key Features

* **Authentication & Authorization**: Knox-based authentication, role-based access (Admin, Customer, Staff), MFA, OAuth.
* **Product Management**: Categories, subcategories, variants, inventory, rich media, reviews & ratings.
* **Order Management**: Persistent carts, order lifecycle, real-time status, history, bulk orders.
* **Payment Processing**: Stripe, PayPal, multi-currency, subscriptions, refunds, analytics.
* **Advanced Features**: GraphQL, Elasticsearch, notifications, recommendations, analytics dashboard.

---

## 🏗️ Tech Stack

* **Backend**: Django, Django REST Framework
* **Database**: PostgreSQL
* **Cache/Queue**: Redis, Celery
* **Auth**: Knox, OAuth
* **Search**: Elasticsearch
* **DevOps**: Docker, GitHub Actions, Nginx, AWS
* **Testing**: Pytest, Factory Boy

---

## 🚀 Quick Start

**1. Clone the project**

```bash
git clone https://github.com/leticiaikemeh/e-commerce.git
cd e-commerce
```

**2. Start with Docker (recommended)**

```bash
docker-compose up --build
```

* API: [http://localhost:8000](http://localhost:8000)
* Admin: [http://localhost:8000/admin](http://localhost:8000/admin)
* Docs: [http://localhost:8000/swagger/](http://localhost:8000/swagger/)

**Manual Setup (without Docker)**

* Install Python 3.9+, PostgreSQL 14+, Redis
* Create & activate virtual environment
* Install dependencies:
  `pip install -r requirements.txt`
* Configure `.env` from `.env.example`
* Run migrations:
  `python manage.py migrate`
* Start server:
  `python manage.py runserver`

---

## 📚 API Documentation

* **Swagger UI**: [http://localhost:8000/swagger/](http://localhost:8000/swagger/)
* **Redoc**: [http://localhost:8000/redoc/](http://localhost:8000/redoc/)
* **GraphQL**: [http://localhost:8000/graphql/](http://localhost:8000/graphql/)

---

## 🧪 Testing

```bash
pytest
# or
python manage.py test
```

---

## 🤝 Contributing

* Fork & clone the repo
* Create a feature branch
* Follow [PEP 8](https://peps.python.org/pep-0008/) and existing code style
* Run tests before PRs

---

## 📄 License

MIT License © 2025 ALX ProDev Backend Engineering Program

---

**Contact**:


