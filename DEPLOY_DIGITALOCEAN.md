# Deploy na DigitalOcean (App Platform) via GitHub

## 1) Criar e ligar repositório no GitHub

No terminal do projeto, execute:

```bash
git add .
git commit -m "prepare project for DigitalOcean App Platform deploy"
git remote add origin https://github.com/SEU_USUARIO/SEU_REPO.git
git push -u origin main
```

## 2) Criar App na DigitalOcean

1. Abra o dashboard da DigitalOcean.
2. Clique em **Create** > **Apps**.
3. Escolha **GitHub** como source e autorize a integração.
4. Selecione o repositório e branch `main`.
5. Em "Configure your app", selecione o arquivo `.do/app.yaml`.
6. Confirme região e tamanho (`basic-xxs` para começar).
7. Crie o app.

## 3) Variáveis e segredo

Durante a criação, confirme estas env vars (já previstas no `app.yaml`):

- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS=.ondigitalocean.app`
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://*.ondigitalocean.app`
- `DJANGO_SECRET_KEY` (segredo gerado por você)
- `DATABASE_URL` (ligado automaticamente ao banco gerenciado)

## 4) Pós deploy

- Verifique logs do serviço web.
- Acesse a URL `*.ondigitalocean.app`.
- Se necessário, rode criação de superusuário em **Console**:

```bash
python manage.py createsuperuser
```

## 5) Domínio próprio (opcional)

- Em App Settings > Domains, adicione seu domínio.
- Atualize DNS (CNAME/A) conforme instruções da DigitalOcean.
- Ajuste `DJANGO_ALLOWED_HOSTS` e `DJANGO_CSRF_TRUSTED_ORIGINS`.
