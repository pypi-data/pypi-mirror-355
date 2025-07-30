def menu():
    menu = """
    =============== MENU ===============

    Seja bem vindo(a)! 💜
    Selecione a operação desejada:

    [1] Depositar
    [2] Sacar
    [3] Exibir Extrato
    [4] Criar Novo Usuário
    [5] Criar Nova Conta Bancária
    [6] Exibir Contas
    [0] SAIR!

    ====================================
    ➡ """
    return input(menu)

def depositar(saldo, valor, extrato, /):
    if valor > 0:
        saldo += valor
        extrato += f"Depósito: R$ {valor:.2f}\n"
        print("\n💲 Depósito realizado com sucesso!")
    else:
        print("\n❌ Operação falhou! Valor informado é inválido. ❌")
    
    return saldo, extrato

def sacar(*, saldo, valor, extrato, limite, nro_saques, limite_saques):
    
    excedeu_saldo = valor > saldo
    excedeu_limite = valor > limite
    excedeu_saques = nro_saques >= limite_saques    

    if excedeu_saldo:
        print("\n❌ Operação falhou! Saldo insuficiente. ❌")
    
    elif excedeu_limite:
        print("\n❌ Operação falhou! Valor do saque excede o limite. ❌")
    
    elif excedeu_saques:
        print("\n❌ Operação falhou! Limite de 3 saques diários atingido, volte amanhã! ❌")

    elif valor > 0:
        saldo -= valor
        extrato += f"Saque: R$ {valor:.2f}\n"
        print("\n💰 Saque realizado com sucesso!")
        return saldo, extrato, True

    else:
        print("\n❌ Operação falhou! Valor informado é inválido.❌")

    return saldo, extrato, False

def exibir_extrato(saldo, /, *, extrato):
    print("\n========== EXTRATO ==========")
    print("Nenhuma movimentação realizada." if not extrato else extrato)
    print(f"\nSaldo: R$ {saldo:.2f}")
    print("=" * 29)

def criar_usuario(usuarios):
    cpf = input("Informe seu CPF (somente números): ")
    usuario = filtrar_usuario(cpf, usuarios)

    if usuario:
        print("\nNão foi possível realizar o cadastro. Já existe usuário com esse CPF!")
        return
    
    nome = input("Informe seu nome completo: ")
    data_nascimento = input("Informe sua data de nascimento (dd-mm-aaaa): ")
    endereco = input("Informe seu endereço (logradouro, nro - bairro - cidade/sigla estado): ")

    usuarios.append({"nome": nome, "data_nascimento": data_nascimento, "cpf": cpf, "endereco": endereco})

    print("\n😎 Usuário criado com sucesso! ")

def filtrar_usuario(cpf, usuarios):
    usuarios_filtrados = [usuario for usuario in usuarios if usuario["cpf"] == cpf]
    return usuarios_filtrados[0] if usuarios_filtrados else None

def criar_conta(agencia, nro_conta, usuarios):
    cpf = input("Informe o CPF do usuário: ")
    usuario = filtrar_usuario(cpf, usuarios)

    if usuario:
        print("\n✔ Conta criada com sucesso! ")
        return {"agencia": agencia, "nro_conta": nro_conta, "usuario": usuario}

    print("\n🙃 Usuário não encontrado, fluxo de criação de conta encerrado! ")

def listar_contas(contas):
    for conta in contas:
        linha = f"""\
            Agência: {conta['agencia']}
            C/C: {conta['nro_conta']}
            Titular: {conta['usuario']['nome']}
        """
        print("=" * 100)
        print(linha)

def main():
    LIMITE_SAQUES = 3
    AGENCIA = "0001"

    saldo = 0
    limite = 500
    extrato = ""
    nro_saques = 0
    usuarios = []
    contas = []

    while True:
        opcao = menu()

        if opcao == "1":
            valor = float(input("Informe o valor do depósito: "))

            saldo, extrato = depositar(saldo, valor, extrato)

        elif opcao == "2":
            valor = float(input("Informe o valor do saque: "))

            saldo, extrato , saque_feito = sacar(
                saldo=saldo,
                valor=valor,
                extrato=extrato,
                limite=limite,
                nro_saques=nro_saques,
                limite_saques=LIMITE_SAQUES,
            )
            if saque_feito:
                nro_saques += 1

        elif opcao == "3":
            exibir_extrato(saldo, extrato=extrato)

        elif opcao == "4":
            criar_usuario(usuarios)

        elif opcao == "5":
            nro_conta = len(contas) + 1
            conta = criar_conta(AGENCIA, nro_conta, usuarios)

            if conta:
                contas.append(conta)

        elif opcao == "6":
            listar_contas(contas)

        elif opcao == "0":
            break

        else:
            print("\n❌ Operação inválida, por favor selecione novamente a operação desejada. ❌")

if __name__ == "__main__":
    main()