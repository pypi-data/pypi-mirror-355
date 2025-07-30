# django-notify

**django-notify** is a simple, plug-and-play Django notification library that supports real-time notifications using Django Channels. It is designed to be **easy to integrate**, **flexible**, and supports **offline message queuing** for users who are not currently connected.

![PyPI - Django Version](https://img.shields.io/badge/Django-3.2%2B-blue)  
![MIT License](https://img.shields.io/badge/license-MIT-green)

---

## 🚀 Features

- 🔌 Easy integration into any Django project
- 📡 Real-time notifications via WebSocket using **Django Channels**
- 💤 Queues messages for offline users and delivers them on reconnect
- 🧠 Supports multiple types of notifications:
  - System Notification (System → User)
  - Single Notification (User → User)
  - Group Notification (User → Many Users)
  - Broadcast Notification (User/System → All/Selected Users)
- ✅ Simple API: send via function or method chaining
- 📦 Designed for extensibility

---

## 📦 Installation

```bash
pip install django-notify-framework

