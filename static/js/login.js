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
                // 🔐 salva o token (IMPORTANTE)
                localStorage.setItem("token", data.access_token);
                localStorage.setItem("id_usuario", data.id_usuario);
                localStorage.setItem("nome_usuario", data.nome);

                // redireciona
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