document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("cadastroForm");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const nome = document.getElementById("nome").value.trim();
        const email = document.getElementById("email").value.trim();
        const senha = document.getElementById("senha").value;
        const confirmarSenha = document.getElementById("confirmar_senha").value;

        // 🔹 validações
        if (!nome || !email || !senha || !confirmarSenha) {
            alert("Preencha todos os campos");
            return;
        }

        if (senha.length < 6) {
            alert("A senha deve ter no mínimo 6 caracteres");
            return;
        }

        if (senha !== confirmarSenha) {
            alert("As senhas não coincidem");
            return;
        }

        try {
            const response = await fetch("/usuario_empresa/cadastro", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    nome,
                    email,
                    senha,
                    confirmar_senha: confirmarSenha // 🔥 opcional mas recomendado
                })
            });

                        let data;

            try {
                data = await response.json();
            } catch {
                data = { detail: "Erro interno do servidor (não retornou JSON)" };
            }

            if (response.ok) {
                alert("Cadastro realizado com sucesso!");
                form.reset();
                window.location.href = "/";
                // 🔥 limpa o formulário
                form.reset();

                // redireciona
                window.location.href = "/";
            } else {
                tratarErro(data);
            }

        } catch (error) {
            alert("Erro ao conectar com o servidor");
            console.error("Erro real:", error);
        }
    });
});

// 🔥 tratamento melhor de erro
function tratarErro(data) {
    if (data.detail) {
        if (Array.isArray(data.detail)) {
            const mensagens = data.detail.map(e => e.msg).join("\n");
            alert(mensagens);
        } else {
            alert(data.detail);
        }
    } else {
        alert("Erro desconhecido");
    }
}