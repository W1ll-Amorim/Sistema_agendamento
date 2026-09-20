# 📅 Sistema de agendamento 

Sistema Web para agendamento de tarefas, desenvolvido com foco em organização e produtividade.

## 🗺️ Roadmap do Projeto

### ✅ Concluído (Base do Sistema)
- [x] Modelagem inicial do banco de dados (SQLite).
- [x] CRUD completo de usuário e agendamentos.
- [x] Funcionalidade de verificação de horários disponíveis.

### 🚧 Em Andamento (Transição para v2.0)
- [x] Migração de banco de dados para PostgreSQL para maior escalabilidade.
- [x] Implementação do Alembic para versionamento do esquema de dados.
- [x] Conteinerização da aplicação (Docker e Docker Compose).
- [ ] Refatoração completa da Interface de Usuário (UI).
- [ ] Ajustes de responsividade para dispositivos móveis.

### 📅 Planejado (Futuro)
- [ ] Integração com sistema de notificações (Email/WhatsApp).
- [ ] Dashboard analítico com métricas de agendamento para administradores.
- [ ] Configuração de pipeline de CI/CD via GitHub Actions.

## 🚀 Tecnologias Utilizadas

![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![APScheduler](https://img.shields.io/badge/APScheduler-blue?style=for-the-badge&logo=python&logoColor=white)
![Git](https://img.shields.io/badge/git-%23F05033.svg?style=for-the-badge&logo=git&logoColor=white)
![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Docker Compose](https://img.shields.io/badge/Docker_Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Alembic](https://img.shields.io/badge/Alembic-4584b6?style=for-the-badge&logo=python&logoColor=white)


---
## 🔐 Segurança

![bcrypt](https://img.shields.io/badge/Hashing-bcrypt-blue)
![JWT](https://img.shields.io/badge/Auth-JWT-black)
![Security](https://img.shields.io/badge/Security-Best%20Practices-green)

---
## 🛠️ Fluxo de Desenvolvimento

### Estratégia de Branching
Este projeto utiliza o modelo de ramificação para garantir a estabilidade da versão principal e organizar o trabalho em equipe:

* **`main`**: Contém o código estável e pronto para uso (produção).
* **`develop`**: Branch de integração para novas funcionalidades antes de irem para a main.
* **`feature/nome-da-feature`**: Branches temporárias para o desenvolvimento de recursos específicos (ex: `feature/agendamento-apscheduler`).

---

## 📌 Funcionalidades

* **Cadastro e histórico de clientes:** Armazena dados dos clientes e histórico de agendamentos para agilizar o atendimento e personalizar o serviço.
* **Planejamento de Tarefas:** Permite que clientes marquem, reagendem ou cancelem consultas/serviços a qualquer hora.
* **Calendário e Disponibilidade em Tempo Real:** Exibe horários disponíveis instantaneamente, evitando choques de agenda e duplicidade de marcações.
* **Gestão de Fila de Espera:** Organiza automaticamente quem aguarda uma vaga, preenchendo horários vagos rapidamente em caso de cancelamento.

---

## ⚙️ Como Rodar o Projeto

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/W1ll-Amorim/Sistema_agendamento.git

## 📸 Screenshots

![Diagrama](static/img/sistema_tela1.png)
![Diagrama](static/img/sistema_tela2.png)
![Diagrama](static/img/sistema_tela3.png)

## 🗄️ Banco de Dados
![Diagrama](static/img/banco01.jpg)
![Diagrama](static/img/banco02.jpg)

## 👨‍💻 Autor Principal
<div align="center">
  <a href="https://github.com/W1ll-Amorim">
    <img src="https://github.com/W1ll-Amorim.png" width="150" alt="Foto de Wiliam de Amorim"/><br>
    <sub><b>Wiliam de Amorim</b></sub>
  </a>
  <br>
  <i>Desenvolvedor Principal</i>
  <br><br>
  <a href="https://www.linkedin.com/in/wiliam-amorim-241784331" target="_blank">
    <img src="https://img.shields.io/badge/-LinkedIn-%230077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn">
  </a>
</div>

---

## 🤝 Contribuidores

| [<img src="https://github.com/Victoroliveira07.png" width=115><br><sub>João Victor</sub>](https://github.com/Victoroliveira07) | [<img src="https://github.com/LilNavaHoods.png" width=115><br><sub>Lohan da Silva</sub>](https://github.com/LilNavaHoods) | [<img src="https://github.com/bielgb13.png" width=115><br><sub>Gabriel Ferreira</sub>](https://github.com/bielgb13) |
| :--- | :--- | :--- |
| <sub>*Vaga aberta para sua PR!*</sub> |
