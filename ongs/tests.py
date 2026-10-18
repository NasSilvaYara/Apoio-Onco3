from django.test import TestCase


class InformacoesViewTests(TestCase):
    def test_each_topic_displays_its_own_content(self):
        temas = {
            'entenda-o-cancer': 'Entenda o câncer',
            'saude-emocional': 'Saúde emocional',
            'autoestima-no-tratamento': 'Autoestima durante o tratamento',
        }

        for slug, titulo in temas.items():
            with self.subTest(tema=slug):
                response = self.client.get(f'/informacoes/{slug}/')

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, titulo)
                self.assertTemplateUsed(response, 'informacoes-para-voce.html')

    def test_unknown_topic_returns_not_found(self):
        response = self.client.get('/informacoes/tema-inexistente/')

        self.assertEqual(response.status_code, 404)
