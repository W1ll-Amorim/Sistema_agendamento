document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("loginForm");

    form.addEventListener("submit", async function(e) {
        e.preventDefault();

        const email = document.querySelector("input[name='email']").value.trim();
        const senha = document.querySelector("input[name='senha']").value;

        // 🔹 validação básica
        if (!email || !senha) {
            alert("Preencha todos os campos");
            return;
        }

        try {
            const response = await fetch("/usuario_empresa/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ email, senha })
            });

            const data = await response.json();

            if (response.ok) {
                // 🔐 Salva as credenciais e estados essenciais no navegador
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('id_usuario', data.id_usuario);
                localStorage.setItem('email', data.email || '');
                localStorage.setItem('nome_usuario', data.nome || '');
                localStorage.setItem('tipo', data.tipo || 'COMUM');

                // Redireciona para o painel principal
                window.location.href = "/telainicial";
            } else {
                alert(data.detail || "Erro no login");
            }

        } catch (error) {
            console.error(error);
            alert("Erro ao conectar com o servidor");
        }
    });
});

// 👁️ Função para mostrar/esconder a senha
function toggleSenha() {
    const inputSenha = document.getElementById("senha");
    const olhoAberto = document.getElementById("icone-olho-aberto");
    const olhoFechado = document.getElementById("icone-olho-fechado");

    if (inputSenha.type === "password") {
        inputSenha.type = "text";
        olhoAberto.style.display = "block";
        olhoFechado.style.display = "none";
    } else {
        inputSenha.type = "password";
        olhoAberto.style.display = "none";
        olhoFechado.style.display = "block";
    }
}
