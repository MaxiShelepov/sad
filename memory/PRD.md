# PRD — WLESS PRO Mobile Port

## Problem Statement
- Пользователь попросил перенести desktop-приложение на Android.
- Требование: максимально сохранить логику ПК-версии, включая лицензию по HWID, профили, fingerprint, одиночный прогрев и режим фермы.

## User Personas
- Основной оператор: управляет профилями, подпиской и прогревом с телефона.
- Владелец подписки: быстро проверяет статус лицензии, HWID и лимиты профилей.
- Продвинутый пользователь: настраивает fingerprint, прокси, режимы прогрева и следит за логами.

## Architecture
- Frontend: Expo Router + React Native (mobile-first Android UI, tabs + stack)
- Backend: FastAPI proxy / adapter
- Runtime Storage: MongoDB только для локальных warmup jobs и логов runtime
- Source of truth for user data: существующий PHP API `https://e-vortex.ru/api.php` и его MySQL-backed backend на стороне сервера пользователя
- State: AsyncStorage для локального HWID, backend для проксирования лицензий/профилей/fingerprint/session/warmup runtime
- Main backend modules:
  - `server.py` — API маршруты
  - `models.py` — Pydantic схемы
  - `remote_vortex.py` — интеграция с живым PHP API
  - `repository.py` — нормализация remote данных и сборка mobile response-моделей
  - `fingerprints.py` — генерация и обновление browser fingerprint
  - `warmup_engine.py` — фоновые задачи прогрева, логи и запись операций обратно в PHP API

## Core Requirements (Static)
- Проверка лицензии по HWID
- Автовыдача trial для нового HWID
- Управление профилями: создание, удаление, batch import
- Сохранение и редактирование fingerprint
- Экран деталей профиля
- Запуск одиночного прогрева с логами, trust score, OPM, progress
- Запуск фермы из нескольких профилей
- Современный Android UI, близкий по ощущению к desktop-версии

## Implemented

### 2026-03-23
- Переписан backend с мобильными API для лицензий, профилей, fingerprint, session data, warmup и farm
- Добавлена логика автотриала по HWID и лимит профилей по подписке
- Добавлен генератор мобильных fingerprint-профилей (browser / OS / screen / timezone / GPU)
- Реализован движок фонового прогрева с логами, статусами, trust score, progress и farm-группами
- Собран Expo mobile UI:
  - вкладки `Лицензия`, `Профили`, `Ферма`
  - stack-экраны `Профиль` и `Отпечаток`
  - форма добавления/импорта профиля
  - карточки профилей и экран логов прогрева
- Добавлены локальное хранение HWID, copy-to-clipboard, адаптация под Android layout
- Проведены backend curl тесты, локальные screenshot-проверки UI и прогон testing agent
- Исправлена проблема цепочки `Профили -> создать профиль -> открыть детали`, список теперь обновляется оптимистично без блокирующего spinner
- Backend переведён с локальной схемы на реальный `e-vortex.ru/api.php`: лицензии, профили, fingerprint, session и stats теперь идут через живой PHP API
- Ключ API оставлен только на backend-стороне; frontend его не получает
- Ключ API вынесен из plaintext-конфига в backend-only runtime secret file и больше не хранится в явном виде в `.env.custom`
- Добавлена обработка upstream-ошибок PHP API через контролируемый 502 вместо traceback 500
- UI полностью переработан в более premium mobile-стиле: deep dark фон, неоновые акценты, стеклянные карточки, плавающий tab bar, более дорогой визуальный ритм
- Добавлена явная UX-подсказка по недоступности farm-режима на trial-подписке
- Исправлены session save/load через живой API key, runtime metrics в detail screen и race на открытии вкладки профилей

## Prioritized Backlog

### P0
- Дополнительно мониторить стабильность внешнего preview-туннеля при публичной проверке
- Добить полностью стабильный web-preview flow `Profiles -> Create -> Open -> Warmup` при сетевой нестабильности внешнего tunnel
- Финально дочистить mobile-web quirks Expo preview (`shadow*` warnings / viewport edge cases), не влияя на Android UX

### P1
- Расширить редактирование профиля (не только создание/удаление)
- Добавить более глубокие метрики прогрева и историю операций по каждому профилю
- Добавить тонкую настройку batch import форматов
- Синхронизировать last action профиля ещё точнее с runtime job metrics

### P2
- Улучшить UI логов: фильтры уровней, автоскролл, пауза лога
- Добавить экран истории подписки и лимитов
- Добавить массовые действия над профилями

## Next Tasks List
- Повторно прогнать полный публичный preview E2E, когда внешний tunnel стабилен
- Добавить редактирование существующего профиля из карточки
- Расширить настройки fingerprint дополнительными пресетами Android/iOS
- Довести сохранение профиля в modal до идеально предсказуемого UX на всех viewport