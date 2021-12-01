#!/usr/bin/bash
export FLASK_ENV=development

echo 'Actual db will be renamed to old_messages_ms.db'
echo 'Remember to rename it if you want to use'
mv -f messages_ms.db old_messages_ms.db || echo 'messages_ms.db not exists... continue with tests'

pytest -s --cov-report term-missing --cov mib

mv -f messages_ms.db messages_ms_test.db
( mv -f old_messages_ms.db messages_ms.db && rm -f messages_ms_test.db ) || ( echo 'old_messages_ms.db not exists... messages_ms.db from test will be held' && mv -f messages_ms_test.db messages_ms.db )

echo 'Test done!'