from unittest.mock import patch

from django.db import OperationalError
from django.test import Client, TestCase, override_settings
from django.utils.html import escape

from oko.models import Card


@override_settings(ALLOWED_HOSTS=["testserver"])
class CardTests(TestCase):
    def test_create_then_open_the_text_card_from_the_collection(self) -> None:
        question = "  Какое слово?\nПодсказка: <b>текст</b>  "
        answer = "  Первая строка\nВторая строка  "
        self.client.cookies["oko_theme"] = "dark"
        self.assertContains(self.client.get("/dashboard/"), 'href="/cards/new/"', count=2)
        self.assertContains(self.client.get("/cards/"), "Здесь пока нет карточек")
        form = self.client.get("/cards/new/")
        self.assertContains(form, 'href="/cards/" aria-current="page"')
        self.assertContains(form, 'data-theme="dark"')
        self.assertIn("Cookie", form.headers["Vary"])

        result = self.client.post("/cards/new/", {"question": question, "answer": answer})
        self.assertRedirects(result, "/cards/")
        card = Card.objects.get()
        self.assertEqual((card.title, card.question, card.answer), ("", question, answer))
        path = f"/cards/{card.pk}/"
        collection = self.client.get("/cards/")
        self.assertContains(collection, f'href="{path}"')
        self.assertContains(collection, escape(question))
        self.assertEqual(Card.objects.count(), 1)

        detail = self.client.get(path)
        self.assertContains(detail, escape(question))
        self.assertContains(detail, escape(answer))
        self.assertContains(detail, 'href="/cards/" aria-current="page"')
        self.assertContains(detail, 'data-theme="dark"')
        self.assertIn("Cookie", detail.headers["Vary"])
        self.assertEqual(self.client.get("/cards/0/").status_code, 404)
        self.assertEqual(self.client.post(path).status_code, 405)

    def test_invalid_sides_keep_the_input_without_writing_a_card(self) -> None:
        response = self.client.post("/cards/new/", {"title": "Моя карточка", "question": "\t \n", "answer": ""})
        self.assertContains(response, "Добавьте текст.")
        self.assertContains(response, "Введите ответ.")
        self.assertContains(response, "Моя карточка")
        self.assertNotContains(response, "Карточка сохранена")
        self.assertFalse(Card.objects.exists())

    def test_write_failure_keeps_the_input_for_retry(self) -> None:
        data = {"title": "Название", "question": "Один вопрос", "answer": "Один ответ"}
        with (
            patch("oko.views.logger") as logger,
            patch("oko.views.CardForm.save", side_effect=OperationalError("Test database is locked")),
        ):
            failed = self.client.post("/cards/new/", data)
        self.assertContains(failed, "Не удалось сохранить карточку", status_code=503)
        self.assertContains(failed, "Один ответ", status_code=503)
        self.assertNotContains(failed, "Test database is locked", status_code=503)
        self.assertNotContains(failed, "Карточка сохранена", status_code=503)
        self.assertFalse(Card.objects.exists())
        logger.error.assert_called_once()
        self.assertRedirects(self.client.post("/cards/new/", data), "/cards/")
        self.assertEqual(Card.objects.get().title, "Название")

    def test_create_requires_csrf(self) -> None:
        client = Client(enforce_csrf_checks=True)
        data = {"question": "Вопрос", "answer": "Ответ"}
        self.assertEqual(client.post("/cards/new/", data).status_code, 403)
        self.assertFalse(Card.objects.exists())
        self.assertContains(client.get("/cards/new/"), 'name="csrfmiddlewaretoken"')
        data["csrfmiddlewaretoken"] = client.cookies["csrftoken"].value
        self.assertRedirects(client.post("/cards/new/", data), "/cards/")
        self.assertEqual(Card.objects.count(), 1)

    def test_save_notification_is_rendered_once_after_the_redirect(self) -> None:
        self.assertNotContains(self.client.get("/cards/"), "Карточка сохранена")
        response = self.client.post("/cards/new/", {"question": "Вопрос", "answer": "Ответ"}, follow=True)
        self.assertEqual(response.redirect_chain, [("/cards/", 302)])
        self.assertContains(response, "Карточка сохранена", count=1)
        self.assertNotContains(self.client.get("/cards/"), "Карточка сохранена")

    def test_next_page_uses_the_shared_notification_template(self) -> None:
        response = self.client.post("/cards/new/", {"question": "Вопрос", "answer": "Ответ"})
        self.assertRedirects(response, "/cards/", fetch_redirect_response=False)
        self.assertContains(self.client.get("/dashboard/"), "Карточка сохранена", count=1)
        self.assertNotContains(self.client.get("/cards/"), "Карточка сохранена")
