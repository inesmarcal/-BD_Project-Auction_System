'''
PROJETO DE BASE DE DADOS 2020/2021 - DEI-UC

Duarte Emanuel Ramos Meneses - 2019216949 - duartemeneses@student.dei.uc.pt
Inês Martins Marçal - 2019215917 - inesmarcal@student.dei.uc.pt
Patricia Beatriz Silva Costa - 2019213995 - patriciacosta@student.dei.uc.pt
'''

from flask import Flask, jsonify, request
import logging, psycopg2, time, datetime

app = Flask(__name__)
sessao = {}


def check_string(string):
    if (string == ""):
        return False
    else:
        return True


## FUNCAO AUXILIAR PARA VER SE O UTILIZADOR ESTÁ BANIDO
def check_ban(userID):
    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT banido FROM utilizador WHERE username LIKE %s", (userID,))

        res = cur.fetchone()

        cur.execute("commit")

        return res[0]
       
    except (Exception, psycopg2.DatabaseError) as error:
        result = 'erro: ' + str(error)
        cur.execute("rollback")
    finally:
        if conn is not None:
            conn.close()
            cur.close()

    return result


## FUNCAO AUXILIAR PARA VER SE JÁ EXISTE UM UTILIZADOR COM O MESMO USERNAME
def check_email(email):
    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM utilizador WHERE email LIKE %s", (email,))

        res = cur.fetchall()

        cur.execute("commit")

        if (res != []):
            return True
        else:
            return False
       
    except (Exception, psycopg2.DatabaseError) as error:
        result = 'erro: ' + str(error)
        cur.execute("rollback")
    finally:
        if conn is not None:
            conn.close()
            cur.close()

    return result


## FUNCAO AUXILIAR PARA VER SE JÁ EXISTE UM UTILIZADOR COM O MESMO USERNAME
def check_username(userID):
    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute('BEGIN TRANSACTION')
        cur.execute("SELECT * FROM utilizador WHERE username LIKE %s", (userID,))

        res = cur.fetchall()

        cur.execute("commit")

        if (res != []):
            return True
        else:
            return False
       
    except (Exception, psycopg2.DatabaseError) as error:
        result = 'erro: ' + str(error)
        cur.execute("rollback")
    finally:
        if conn is not None:
            conn.close()
            cur.close()

    return result


## ADICIONAR UM UTILIZADOR
@app.route("/dbproj/user", methods=['POST'])
def add_user():
    logger.info("###              ADICIONAR UTILIZADOR             ###");   
    payload = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    try:
        username = request.form['username']

        if check_string(username):
            if (check_username(username) == False):

                email = request.form['email']
                if check_string(email):
                    if (check_email(email) == False):
                        password = request.form['password']

                        if check_string(password):

                            # parameterized queries, good for security and performance
                            statement = """
                                        INSERT INTO utilizador (username, email, password, administrador, banido) 
                                                VALUES ( %s,   %s ,   %s ,   %s,   %s)"""

                            values = (username, email, password, False, False)

                            cur.execute("BEGIN TRANSACTION")
                            cur.execute("lock table utilizador in exclusive mode")
                            cur.execute(statement, values)
                            cur.execute("commit")
                            result = {'userId: ' :username}
                        else:
                            result = {'erro': 'Password invalida'} 
                    else:
                        result = {'erro': 'Já existe um utilizador com esse email'} 
                else:
                    result = {'erro': 'Email invalido'} 
            else:
                result = {'erro': 'Já existe um utilizador com esse username'} 
        else:
            result = {'erro': 'Username invalido'} 
    except (Exception, psycopg2.DatabaseError) as error:
        result = {'erro': str(error)} 
        cur.execute("ROLLBACK")
    finally:
        if conn is not None:
            conn.close()
            cur.close()

    return jsonify(result)


## FUNCAO AUXILIAR QUE GERA O TOKEN DE CADA UTILIZADOR
def gera_token(user_id):
    token = ""
    for i in range(len(user_id)):
        c = ord(user_id[i]) + 3
        token += chr(c)
    return token


## FUNCAO AUXILIAR PARA VER SE EXISTE UM UTILIZADOR COM AQUELA PASSWORD
def existe_user_pass(username, password):

    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute('BEGIN TRANSACTION')
        cur.execute("SELECT password FROM utilizador WHERE utilizador.username LIKE %s", (username,) )

        res = cur.fetchone()

        if (res[0] == password):
            cur.execute("commit")
            return True
        else:
            cur.execute("commit")
            return False

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        cur.execute("rollback")
    finally:
        if conn is not None:
            conn.close()
            cur.close()


## FUNCAO AUXILIAR PARA VER SE O TOKEN ESTA VALIDO
def authenticate_user_token(token):

    conn = db_connection()
    cur = conn.cursor()

    if (token in sessao.keys()):
        validade = sessao[token]
        atual = datetime.datetime.now()

        if (validade > atual):
            try:
                cur.execute("BEGIN TRANSACTION")
                cur.execute("SELECT username FROM utilizador WHERE token LIKE %s", (token,) )
                user = cur.fetchone()
                cur.execute("commit")

                return user[0]

            except (Exception, psycopg2.DatabaseError) as error:
                    result = 'erro: ' + str(error)
                    cur.execute("rollback")
            finally:
                if conn is not None:
                    conn.close()
                    cur.close()

        else:
            return 'erro: AuthError'
    else:
        return 'erro: AuthError'

    
## AUTENTICACAO
@app.route("/dbproj/user", methods=['PUT'])
def authenticate_user():
    logger.info("###              AUTENTICACAO              ###");   

    conn = db_connection()
    cur = conn.cursor()

    try:
        username = request.form['username']
        password = request.form['password']

        if (existe_user_pass(username, password)):
            if (check_ban(username) == False):
                
                authToken = gera_token(username)    
                sessao[authToken] = datetime.datetime.now() + datetime.timedelta(minutes=20)

                cur.execute("BEGIN TRANSACTION")
                cur.execute("lock table utilizador in exclusive mode")
                cur.execute("UPDATE utilizador SET token = %s WHERE username = %s", (str(authToken), username,))

                result = {'authToken: ' : authToken}

                cur.execute("commit")

            else:
                result = {'erro' :'Utilizador banido'}  
        else:
            result = {'erro' :'AuthError'}  

    except (Exception, psycopg2.DatabaseError) as error:
        result = {'erro' :str(error)}  
        cur.execute("rollback")
    finally:
        if conn is not None:
            conn.close()
            cur.close()

    return jsonify(result)


## FUNCAO AUXILIAR QUE PERMITE AFERIR SE JÁ EXISTE UM LEILAO COM AQUELE CODIGO
def check_codigo(codigo):
    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute("BEGIN TRANSACTION")
        cur.execute("SELECT count(*) FROM leilao WHERE leilao.codigo_artigo LIKE %s", (codigo,) )

        res = cur.fetchone()

        if (int(res[0]) == 0):
            cur.execute("commit")
            return False
        else:
            cur.execute("commit")
            return True

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        cur.execute("rollback")
    finally:
        if conn is not None:
            conn.close()
            cur.close()


## CRIAR UM LEILAO
@app.route("/dbproj/leilao", methods=['POST'])
def add_leilao():
    logger.info("###              CRIAR UM LEILAO              ###");   

    conn = db_connection()
    cur = conn.cursor()

    try:
        token = request.form['token']

        user = authenticate_user_token(token)

        if user != 'erro: AuthError':
            if (check_ban(user) == False):
                
                codigo_artigo = request.form['codigo_artigo']
                if check_string(codigo_artigo):
                    if check_codigo(codigo_artigo) == False:
                        titulo = request.form['titulo']
                        if check_string(titulo):
                            data_hora_fim = request.form['data_hora_fim'] 
                            if check_string(data_hora_fim):
                                detalhes_adicionais = request.form['detalhes_adicionais']
                                preco_minimo = request.form['preco_minimo']
                                if (int(preco_minimo) > 0):
                                    descricao_atual = request.form['descricao_atual']

                                    # parameterized queries, good for security and performance
                                    statement = """
                                                INSERT INTO leilao (codigo_artigo, titulo, data_hora_fim, detalhes_adicionais, preco_minimo, encerrado, descricao_atual, utilizador_username) 
                                                        VALUES ( %s,   %s ,   %s ,   %s,   %s,   %s ,   %s,   %s)"""

                                    values = (codigo_artigo, titulo, data_hora_fim, detalhes_adicionais, preco_minimo, False, descricao_atual, user)

                                    cur.execute("BEGIN TRANSACTION")
                                    cur.execute("lock table leilao in exclusive mode")
                                    cur.execute(statement, values)

                                    cur.execute("SELECT max(id) FROM historico")

                                    id_max = cur.fetchone()

                                    if(id_max[0] == None):
                                        novo_id = 1
                                    else:
                                        novo_id = int(id_max[0])+1

                                    statement = """
                                            INSERT INTO historico (descricao, data, leilao_codigo_artigo, titulo, detalhes_adicionais, id)
                                                    VALUES ( %s,   %s ,   %s, %s, %s, %s)"""

                                    data = datetime.datetime.now()
                                                    
                                    values = (descricao_atual, data, codigo_artigo, titulo, detalhes_adicionais, novo_id)

                                    cur.execute("lock table historico in exclusive mode")
                                    cur.execute(statement, values)

                                    cur.execute("commit")
                                    result = {'leilaoID: ' : codigo_artigo}
                            
                                else:
                                    result = {'erro': 'Preco minimo invalido'}
                            else:
                                result = {'erro': 'Data invalida'}
                        else:
                            result = {'erro': 'Titulo invalido'}
                    else:
                        result = {'erro': 'Já existe um leilão com o mesmo ID'}
                else:
                    result = {'erro': 'Codigo de artigo invalido'} 
            else:
                result = {'erro' :'Utilizador banido'}
        else:
            result = {'erro': 'AuthError'}

    except (Exception, psycopg2.DatabaseError) as error:
        cur.execute("rollback")
        result = {'erro': str(error)}
    finally:
        if conn is not None:
            conn.close()
            cur.close()

    return jsonify(result)


## OBTER TODOS OS LEILOES
@app.route("/dbproj/leiloes", methods=['GET'], strict_slashes=True)
def get_all_leiloes():
    logger.info("###              OBTER DETALHES DE TODOS OS LEILOES             ###");   

    conn = db_connection()
    cur = conn.cursor()

    end_leilao()

    try:
        token = request.form['token']

        user = authenticate_user_token(token)

        if user != 'erro: AuthError':
            if (check_ban(user) == False):
                    cur.execute("BEGIN TRANSACTION")
                    cur.execute("SELECT codigo_artigo, descricao_atual FROM leilao WHERE encerrado = %s", (False,))
                    rows = cur.fetchall()

                    payload = []
                    for row in rows:
                        logger.debug(row)
                        content = {'leilaoID': row[0], 'descricao': row[1]}
                        payload.append(content) # appending to the payload to be returned
                    
                    cur.execute("commit")

            else:
                return jsonify('Utilizador banido')
        else:
            return jsonify(user)

    except (Exception, psycopg2.DatabaseError) as error:
        cur.execute("rollback")
        return jsonify('erro: ' + str(error)) 
    finally:
        if conn is not None:
            conn.close()
            cur.close()

    return jsonify(payload)


## OBTER ID E DESCRICAO DE UM LEILAO PELO ID OU DESCRICAO
@app.route("/dbproj/leiloes/<keyword>", methods=['GET'])
def get_leilao(keyword):
    logger.info("###              OBTER ID E DESCRICAO DE UM LEILAO PELO ID OU DESCRICAO             ###");   

    logger.debug(f'keyword: {keyword}')

    conn = db_connection()
    cur = conn.cursor()

    end_leilao()

    try:
        token = request.form['token']

        user = authenticate_user_token(token)

        if user != 'erro: AuthError':
            if (check_ban(user) == False):
                    cur.execute("BEGIN TRANSACTION")
                    cur.execute("SELECT codigo_artigo, descricao_atual FROM leilao where (codigo_artigo = %s or descricao_atual LIKE %s) and encerrado = %s", (keyword, keyword, False,) )

                    rows = cur.fetchall()

                    payload = []

                    if (rows != []):
                        for row in rows:
                            content = {'leilaoID': row[0], 'descricao': row[1]}
                            payload.append(content)

                    else:
                        res = 'erro: Leilao nao encontrado'
                        return jsonify(res)

                    cur.execute("commit")
                
            else:
                return jsonify('Utilizador banido')
        else:
            return jsonify(user)

    except (Exception, psycopg2.DatabaseError) as error:
        cur.execute("rollback")
        return jsonify('erro: ' + str(error)) 
    finally:
        if conn is not None:
            conn.close()
            cur.close()

    return jsonify(payload)


## OBTER DETALHES DE UM LEILAO (AUXILIAR)
def obtem_todos_detalhes(leilaoID):

    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute("BEGIN TRANSACTION")
        cur.execute("SELECT codigo_artigo, descricao_atual, titulo, data_hora_fim, detalhes_adicionais, preco_minimo, encerrado, licitacao_atual, utilizador_username, vencedor FROM leilao WHERE codigo_artigo = %s", (leilaoID,) )

        rows = cur.fetchall()

        payload = []

        if (rows != []):

            row = rows[0]

            content = {'leilaoID': row[0], 'descricao': row[1], 'titulo': row[2], 'data_hora_fim': row[3], 'detalhes_adicionais': row[4], 'preco_minimo': row[5], 'encerrado': row[6], 'licitacao_atual': row[7], 'criador_leilao': row[8], 'vencedor': row[9] }
            payload.append(content)

            cur.execute("SELECT mensagens, data_mensagem, mensagens_leilao.utilizador_username FROM mensagens_leilao WHERE leilao_codigo_artigo = %s", (leilaoID,) )

            rows = cur.fetchall()

            if (rows != []):

                for row in rows:
                    content = {'mensagens' : row[0], 'data_mensagem' : row[1], 'utilizador_username' : row[2]}
                    payload.append(content)
            
            else: 
                content = {'mensagens' : 'Sem mensagens'} 
                payload.append(content)      

            cur.execute("SELECT id, valor, data, valida, licitacao.utilizador_username FROM licitacao WHERE leilao_codigo_artigo = %s", (leilaoID,) )

            rows = cur.fetchall()

            if (rows != []):

                for row in rows:
                    content={'id_licitacao' : row[0], 'valor_licitacao' : row[1], 'data_licitacao' : row[2], 'licitacao_valida' : row[3], 'username_licitacao' : row[4]}
                    payload.append(content)     

            else: 
                content = {'licitacao' : 'No bids'}
                payload.append(content)       

        else:
            cur.execute("commit")
            res = 'error: Auction not found'
            return res

        cur.execute("commit")
        
    except (Exception, psycopg2.DatabaseError) as error:
        cur.execute("rollback")
        return 'erro: ' + str(error)
    finally:
        if conn is not None:
            conn.close()
            cur.close()

    return payload


## OBTER DETALHES DE UM LEILAO
@app.route("/dbproj/leilao/<leilaoID>", methods=['GET'])
def get_detalhes_leilao(leilaoID):
    logger.info("###              OBTER DETALHES DE UM LEILAO            ###");   

    logger.debug(f'leilaoID: {leilaoID}')

    try:
        token = request.form['token']

        user = authenticate_user_token(token)

        if user != 'erro: AuthError':
            if (check_ban(user) == False):
                payload = obtem_todos_detalhes(leilaoID)
            else:
                return jsonify('Utilizador banido')
        else:
            return jsonify(user)

    except (Exception, psycopg2.DatabaseError) as error:
        return jsonify('erro: ' + str(error))
 
    return jsonify(payload)


## OBTER OS LEILOES EM QUE UM UTILIZADOR PARTICIPA
@app.route("/dbproj/leiloes_user", methods=['GET'], strict_slashes=True)
def get_leiloes_user():
    logger.info("###              OBTER OS LEILOES EM QUE UM UTILIZADOR PARTICIPA             ###");   

    leiloes_id = []

    conn = db_connection()
    cur = conn.cursor()

    try:
        token = request.form['token']

        user = authenticate_user_token(token)

        if user != 'erro: AuthError':
            if (check_ban(user) == False):
                cur.execute("BEGIN TRANSACTION")
                cur.execute("SELECT codigo_artigo, descricao_atual, titulo, data_hora_fim, detalhes_adicionais, preco_minimo, encerrado, licitacao_atual, vencedor FROM leilao WHERE utilizador_username LIKE %s", (user,) )
                rows = cur.fetchall()


                if (rows != []):
                    payload = []
                    for row in rows:
                        logger.debug(row)
                        leiloes_id.append(row[0])
                        content = {'codigo_artigo' : row[0], 'descricao_atual' : row[1], 'titulo': row[2], 'data_hora_fim' : row[3], 'detalhes_adicionais' : row[4], 'preco_minimo' : row[5], 'encerrado' : row[6], 'licitacao_atual' : row[7], 'vencedor': row[8]}
                        payload.append(content) # appending to the payload to be returned


                cur.execute("SELECT leilao_codigo_artigo FROM licitacao WHERE utilizador_username LIKE %s", (user,) )
                rows = cur.fetchall()

                if (rows != []):
                    for row in rows:
                        if (row[0] not in leiloes_id):
                            leiloes_id.append(row[0])

                            cur.execute("SELECT codigo_artigo, descricao_atual, titulo, data_hora_fim, detalhes_adicionais, preco_minimo, encerrado, licitacao_atual, vencedor FROM leilao WHERE codigo_artigo = %s", (row[0],) )
                            rows1 = cur.fetchall()

                            if (rows1 != []):
                                for row1 in rows1:
                                    leiloes_id.append(row1[0])
                                    content = {'codigo_artigo': row1[0], 'descricao_atual' : row1[1], 'titulo' : row1[2], 'data_hora_fim' : row1[3], 'detalhes_adicionais' : row1[4], 'preco_minimo' : row1[5], 'encerrado' : row1[6], 'licitacao_atual' :row1[7], 'vencedor': row1[8]}
                                    payload.append(content) # appending to the payload to be returned
 
                
                cur.execute("commit")
            else:
                return('Utilizador banido')
        else:
            return jsonify(user)

    except (Exception, psycopg2.DatabaseError) as error:
        cur.execute("rollback")
        return jsonify('erro: ' + str(error))
    finally:
        if conn is not None:
            conn.close()
            cur.close()

    return jsonify(payload)


## FAZER LICITACAO
@app.route("/dbproj/licitar/<leilaoID>/<licitacao>", methods=['POST'])
def do_licitacao(leilaoID, licitacao):
    logger.info("###              FAZER LICITACAO             ###");   

    logger.debug(f'leilaoID: {leilaoID}')
    logger.debug(f'licitacao: {licitacao}')

    conn = db_connection()
    cur = conn.cursor()

    end_leilao()

    try:
        token = request.form['token']

        user = authenticate_user_token(token)

        if user != 'erro: AuthError':
            if (check_ban(user) == False):
                cur.execute("BEGIN TRANSACTION")
                cur.execute("SELECT licitacao_atual, preco_minimo, encerrado, utilizador_username FROM leilao WHERE codigo_artigo = %s", (leilaoID,) )
                rows = cur.fetchone()

                if (rows == None):
                    return jsonify('Leilao nao existe')
                elif ((rows[0] == None) and (rows[1] != None)):
                    atual = 0
                elif (rows[0] != None):
                    atual = rows[0]


                if (rows[3] != user):
                    if (int(licitacao) > atual):
                        if (int(licitacao) >= int(rows[1])):
                            if (rows[2] == False):
                                cur.execute("lock table leilao in exclusive mode")
                                cur.execute("UPDATE leilao SET licitacao_atual = %s WHERE codigo_artigo = %s", (licitacao, leilaoID) )

                                cur.execute("SELECT max(id) FROM licitacao")

                                id_max = cur.fetchone()

                                if(id_max[0] == None):
                                    novo_id = 1
                                else:
                                    novo_id = int(id_max[0])+1

                                data = datetime.datetime.now()

                                statement = """
                                        INSERT INTO licitacao (id, valor, data, valida, utilizador_username, leilao_codigo_artigo) 
                                                VALUES ( %s,   %s ,   %s ,   %s,   %s,   %s )"""

                                values = (str(novo_id), licitacao, data, True, user, leilaoID)

                                cur.execute("lock table licitacao in exclusive mode")
                                cur.execute(statement, values)

                                ### MENSAGEM NO MURAL DE QUEM LICITOU ###

                                cur.execute("SELECT utilizador_username FROM licitacao WHERE leilao_codigo_artigo = %s", (leilaoID,))

                                ja_enviado = [user]

                                a_enviar = cur.fetchall()

                                for row in a_enviar:
                                    if (row[0] not in ja_enviado):
                                        ja_enviado.append(row[0])

                                        cur.execute("SELECT max(id) FROM mensagens_utilizador")

                                        id_max = cur.fetchone()

                                        if(id_max[0] == None):
                                            novo_id = 1
                                        else:
                                            novo_id = int(id_max[0])+1

                                        mensagem = 'Licitação ultrapassada no leilão com o código ' + leilaoID
                                        remetente = 'Sistema do leilão com o código ' + leilaoID

                                        statement = """
                                                        INSERT INTO mensagens_utilizador (mensagens, data_mensagem, lido, id, remetente, leilao_codigo_artigo, utilizador_username) 
                                                                VALUES ( %s,   %s , %s, %s, %s,  %s ,   %s)"""

                                        values = (mensagem, data, False, str(novo_id), remetente, leilaoID, row[0])

                                        cur.execute("lock table mensagens_utilizador in exclusive mode")
                                        cur.execute(statement, values)


                                result = 'Sucesso'

                            else:
                                result = 'Leilão já não aceita licitações'
                        else:
                            result = 'Licitacao inferior ao preço minimo pedido pelo criador do leilao'
                    else:
                        result = 'Licitacao igual ou inferior à atual'
                else:
                    result = 'O criador do leilão não pode licitar o mesmo'

                cur.execute("commit")

            else:
                return jsonify('Utilizador banido')
        else:
            return jsonify(user)

    except (Exception, psycopg2.DatabaseError) as error:
        cur.execute("rollback")
        result = 'erro: ' + str(error)
    finally:
        if conn is not None:
            conn.close()
            cur.close()

    return jsonify(result)
    

## EDITAR PROPRIEDADES DE LEILAO
@app.route("/dbproj/leilao/<leilaoID>", methods=['PUT'])
def edit_prop_leilao(leilaoID):
    logger.info("###              EDITAR PROPRIEDADES DE LEILAO           ###");   

    logger.debug(f'leilaoID: {leilaoID}')

    conn = db_connection()
    cur = conn.cursor()

    try:
        token = request.form['token']
        parametro = request.form['parametro']
        nova_desc = request.form['nova_desc']

        user = authenticate_user_token(token)

        if user != 'erro: AuthError':
            if (check_ban(user) == False):
                if ((check_string(nova_desc) == True) or ((check_string(nova_desc) == False) and (parametro == 'detalhes_adicionais'))):

                    cur.execute("BEGIN TRANSACTION")
                    cur.execute("SELECT codigo_artigo FROM leilao WHERE codigo_artigo = %s", (leilaoID,))

                    res = cur.fetchone()

                    if res != None:  
                        cur.execute("SELECT utilizador_username FROM leilao WHERE codigo_artigo = %s", (leilaoID,))

                        res = cur.fetchone()

                        if (res[0] == user):
                            if (parametro == 'titulo'):
                                cur.execute("lock table leilao in exclusive mode")
                                cur.execute("UPDATE leilao SET titulo = %s WHERE codigo_artigo = %s", (nova_desc, leilaoID))

                                cur.execute("SELECT descricao_atual, titulo, detalhes_adicionais FROM leilao WHERE codigo_artigo = %s", (leilaoID,))

                                des = cur.fetchone()

                                cur.execute("SELECT max(id) FROM historico")

                                id_max = cur.fetchone()

                                if(id_max[0] == None):
                                    novo_id = 1
                                else:
                                    novo_id = int(id_max[0])+1

                                statement = """
                                            INSERT INTO historico (descricao, data, titulo, detalhes_adicionais, leilao_codigo_artigo, id)
                                                    VALUES ( %s,   %s ,   %s, %s, %s, %s )"""

                                data = datetime.datetime.now()
                                                
                                values = (des[0], data, des[1], des[2], leilaoID, novo_id)

                                cur.execute("lock table historico in exclusive mode")
                                cur.execute(statement, values)

                                result = obtem_todos_detalhes(leilaoID)

                            elif (parametro == 'detalhes_adicionais'):
                                cur.execute("UPDATE leilao SET detalhes_adicionais = %s WHERE codigo_artigo = %s", (nova_desc, leilaoID))

                                cur.execute("SELECT descricao_atual, titulo, detalhes_adicionais FROM leilao WHERE codigo_artigo = %s", (leilaoID,))

                                des = cur.fetchone()

                                cur.execute("SELECT max(id) FROM historico")

                                id_max = cur.fetchone()

                                if(id_max[0] == None):
                                    novo_id = 1
                                else:
                                    novo_id = int(id_max[0])+1

                                statement = """
                                            INSERT INTO historico (descricao, data, titulo, detalhes_adicionais, leilao_codigo_artigo, id)
                                                    VALUES ( %s,   %s ,   %s, %s, %s, %s )"""

                                data = datetime.datetime.now()
                                                
                                values = (des[0], data, des[1], des[2], leilaoID, novo_id)

                                cur.execute(statement, values)

                                result = obtem_todos_detalhes(leilaoID)

                            elif (parametro == 'descricao_atual'):
                                cur.execute("UPDATE leilao SET descricao_atual = %s WHERE codigo_artigo = %s", (nova_desc, leilaoID))

                                cur.execute("SELECT descricao_atual, titulo, detalhes_adicionais FROM leilao WHERE codigo_artigo = %s", (leilaoID,))

                                des = cur.fetchone()

                                cur.execute("SELECT max(id) FROM historico")

                                id_max = cur.fetchone()

                                if(id_max[0] == None):
                                    novo_id = 1
                                else:
                                    novo_id = int(id_max[0])+1

                                statement = """
                                            INSERT INTO historico (descricao, data, titulo, detalhes_adicionais, leilao_codigo_artigo, id)
                                                    VALUES ( %s,   %s ,   %s, %s, %s, %s )"""

                                data = datetime.datetime.now()
                                                
                                values = (des[0], data, des[1], des[2], leilaoID, novo_id)

                                cur.execute(statement, values)

                                result = obtem_todos_detalhes(leilaoID)

                            else:
                                result = {'erro':'Parametro não pode ser alterado'}

                        else:
                            result = {'erro': 'ID de leilão não corresponde a um leilão desse utilizador'}
                    else:
                        result = {'erro' :'ID de leilão não corresponde a nenhum leilão existente'}

                    cur.execute("commit")

                else:
                    result = {'erro' : 'Descrição inválido'}
            else:
                result = {'erro' : 'Utilizador banido'}
        else: 
            result = {'erro': user}

    except (Exception, psycopg2.DatabaseError) as error:
        result = {'erro': str(error)}
        cur.execute("rollback")
    finally:
        if conn is not None:
            conn.close()
            cur.close()

    return jsonify(result)


## PUBLICAR MENSAGEM (AUXILIAR)
def escrever_mensagem_leilao(leilaoID, user, mensagem, licitadores):
    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute("BEGIN TRANSACTION")
        cur.execute("SELECT utilizador_username FROM leilao WHERE codigo_artigo = %s", (leilaoID,))

        criador = cur.fetchone()

        if criador != None:

            ### MENSAGEM NO MURAL DO LEILAO ###

            cur.execute("SELECT max(id) FROM mensagens_leilao")

            id_max = cur.fetchone()

            if(id_max[0] == None):
                novo_id = 1
            else:
                novo_id = int(id_max[0])+1

            data = datetime.datetime.now()

            statement = """
                            INSERT INTO mensagens_leilao (mensagens, data_mensagem, id, utilizador_username, leilao_codigo_artigo) 
                                    VALUES ( %s,   %s , %s,  %s ,   %s)"""

            values = (mensagem, data, str(novo_id), user, leilaoID)

            cur.execute("lock table mensagens_leilao in exclusive mode")
            cur.execute(statement, values)

            ### MENSAGEM NO MURAL DO CRIADOR DO LEILAO ###

            if (user != criador[0]):
                cur.execute("SELECT max(id) FROM mensagens_utilizador")

                id_max = cur.fetchone()

                if(id_max[0] == None):
                    novo_id = 1
                else:
                    novo_id = int(id_max[0])+1


                statement = """
                                INSERT INTO mensagens_utilizador (mensagens, data_mensagem, lido, id, remetente, leilao_codigo_artigo, utilizador_username) 
                                        VALUES ( %s,   %s , %s, %s, %s,  %s ,   %s)"""

                values = (mensagem, data, False, str(novo_id), user, leilaoID, criador)

                cur.execute("lock table mensagens_utilizador in exclusive mode")
                cur.execute(statement, values)

            ### MENSAGEM NO MURAL DE QUEM ESCREVEU NO MURAL DO LEILAO ###

            cur.execute("SELECT utilizador_username FROM mensagens_leilao WHERE leilao_codigo_artigo = %s", (leilaoID,))

            ja_enviado = [criador[0], user]

            a_enviar = cur.fetchall()

            for row in a_enviar:
                if (row[0] not in ja_enviado):
                    ja_enviado.append(row[0])

                    cur.execute("SELECT max(id) FROM mensagens_utilizador")

                    id_max = cur.fetchone()

                    if(id_max[0] == None):
                        novo_id = 1
                    else:
                        novo_id = int(id_max[0])+1


                    statement = """
                                    INSERT INTO mensagens_utilizador (mensagens, data_mensagem, lido, id, remetente, leilao_codigo_artigo, utilizador_username) 
                                            VALUES ( %s,   %s , %s, %s, %s,  %s ,   %s)"""

                    values = (mensagem, data, False, str(novo_id), user, leilaoID, row[0])

                    cur.execute(statement, values)

            if (licitadores == 'sim'):
                cur.execute("SELECT utilizador_username FROM licitacao WHERE leilao_codigo_artigo = %s", (leilaoID,))

                a_enviar = cur.fetchall()

                for row in a_enviar:
                    if (row[0] not in ja_enviado):
                        ja_enviado.append(row[0])

                        cur.execute("SELECT max(id) FROM mensagens_utilizador")

                        id_max = cur.fetchone()

                        if(id_max[0] == None):
                            novo_id = 1
                        else:
                            novo_id = int(id_max[0])+1


                        statement = """
                                        INSERT INTO mensagens_utilizador (mensagens, data_mensagem, lido, id, remetente, leilao_codigo_artigo, utilizador_username) 
                                                VALUES ( %s,   %s , %s, %s, %s,  %s ,   %s)"""

                        values = (mensagem, data, False, str(novo_id), user, leilaoID, row[0])

                        cur.execute(statement, values)

            result = 'Sucesso'

        else:
            result = 'ID de leilão não corresponde a nenhum existente'
 
        cur.execute("commit")

    except (Exception, psycopg2.DatabaseError) as error:
        cur.execute("rollback")
        result = 'erro: ' + str(error)
    finally:
        if conn is not None:
            conn.close()
            cur.close()

    return result


## PUBLICAR MENSAGEM NO MURAL DE UM LEILAO 
@app.route("/dbproj/mensagem_leilao/<leilaoID>", methods=['POST'])
def write_leilao_message(leilaoID):

    logger.info("###              PUBLICAR MENSAGEM NO MURAL DE UM LEILAO       ###");   

    logger.debug(f'leilaoID: {leilaoID}')

    try:
        token = request.form['token']
        mensagem = request.form['mensagem']

        if check_string(mensagem):
            user = authenticate_user_token(token)

            if user != 'erro: AuthError':
                if (check_ban(user) == False):
                    result = escrever_mensagem_leilao(leilaoID, user, mensagem, 'nao')
                else:
                    return jsonify('Utilizador banido')
            else:
                return jsonify(user)
        
        else:
            result = 'erro: Mensagem vazia'

    except (Exception, psycopg2.DatabaseError) as error:
        result = 'erro: ' + str(error)

    return jsonify(result)


## RECEBER MENSAGENS
@app.route("/dbproj/recebermens", methods=['GET'])
def get_mensagens_user():
    logger.info("###              RECEBER MENSAGENS          ###");   

    conn = db_connection()
    cur = conn.cursor()

    try:
        token = request.form['token']

        user = authenticate_user_token(token)

        if user != 'erro: AuthError':
            if (check_ban(user) == False):
                cur.execute("BEGIN TRANSACTION")
                cur.execute("SELECT mensagens, data_mensagem, remetente, leilao_codigo_artigo, id FROM mensagens_utilizador WHERE utilizador_username = %s and lido = False", (user,))

                mens = cur.fetchall()
                payload = []
                ids = []

                if mens != []:

                    for row in mens:
                        content = {'mensagem': row[0], 'data_mensagem': row[1], 'remetente': row[2], 'codigo_artigo': row[3]}
                        ids.append(row[4])
                        payload.append(content) # appending to the payload to be returned

                    for id in ids:
                        cur.execute("lock table mensagens_utilizador in exclusive mode")
                        cur.execute("UPDATE mensagens_utilizador SET lido = %s WHERE id = %s", (True, id))

                    cur.execute("commit")
                    return jsonify(payload)

                else:
                    cur.execute("commit")
                    result = 'Não há mensagens novas'

            else:
                return jsonify('Utilizador banido')
        else:
            return jsonify(user)

    except (Exception, psycopg2.DatabaseError) as error:
        cur.execute("rollback")
        result = 'erro: ' + str(error)
    finally:
        if conn is not None:
            conn.close()
            cur.close()

    return jsonify(result)


## CANCELAR LEILAO (AUXILIAR)
def cancelar_leilao(user, leilaoID):

    conn = db_connection()
    cur = conn.cursor()

    try:
        cur.execute("BEGIN TRANSACTION")
        cur.execute("SELECT administrador FROM utilizador WHERE username LIKE %s", (user,))
        
        admin = cur.fetchone()

        if (admin[0] == True):

            cur.execute("SELECT encerrado FROM leilao WHERE codigo_artigo = %s", (leilaoID,))

            cancel = cur.fetchone()

            if (cancel == None):
                result = 'Leilão não encontrado'

            elif (cancel[0] == False):
                cur.execute("lock table leilao in exclusive mode")
                cur.execute("UPDATE leilao SET encerrado = %s WHERE codigo_artigo = %s", (True, leilaoID))

                cur.execute("SELECT utilizador_username FROM leilao WHERE codigo_artigo = %s", (leilaoID,))

                ja_enviado = []
                mensagem = 'Leilão com o código ' + leilaoID + ' cancelado'
                data = datetime.datetime.now()
                remetente = 'Sistema do leilão com o código ' + leilaoID

                ### MANDAR MENSAGEM PARA O CRIADOR ###

                criador = cur.fetchone()

                cur.execute("SELECT max(id) FROM mensagens_utilizador")

                id_max = cur.fetchone()

                if(id_max[0] == None):
                    novo_id = 1
                else:
                    novo_id = int(id_max[0])+1

                statement = """
                                INSERT INTO mensagens_utilizador (mensagens, data_mensagem, lido, id, remetente, leilao_codigo_artigo, utilizador_username) 
                                        VALUES ( %s,   %s , %s, %s, %s,  %s ,   %s)"""

                values = (mensagem, data, False, str(novo_id), remetente, leilaoID, criador[0])

                cur.execute("lock table mensagens_utilizador in exclusive mode")
                cur.execute(statement, values)

                ja_enviado.append(criador[0])

                ### MANDAR MENSAGEM PARA QUEM LICITOU ###

                cur.execute("SELECT utilizador_username FROM licitacao WHERE leilao_codigo_artigo = %s", (leilaoID,))

                a_enviar = cur.fetchall()

                for row in a_enviar:
                    if (row[0] not in ja_enviado):
                        ja_enviado.append(row[0])

                        cur.execute("SELECT max(id) FROM mensagens_utilizador")

                        id_max = cur.fetchone()

                        if(id_max[0] == None):
                            novo_id = 1
                        else:
                            novo_id = int(id_max[0])+1

                        statement = """
                                        INSERT INTO mensagens_utilizador (mensagens, data_mensagem, lido, id, remetente, leilao_codigo_artigo, utilizador_username) 
                                                VALUES ( %s,   %s , %s, %s, %s,  %s ,   %s)"""

                        values = (mensagem, data, False, str(novo_id), remetente, leilaoID, row[0])

                        cur.execute(statement, values)

                ### MANDAR MENSAGEM PARA QUEM ESCREVEU NO MURAL ###

                cur.execute("SELECT utilizador_username FROM mensagens_leilao WHERE leilao_codigo_artigo = %s", (leilaoID,))

                a_enviar = cur.fetchall()

                for row in a_enviar:
                    if (row[0] not in ja_enviado):
                        ja_enviado.append(row[0])

                        cur.execute("SELECT max(id) FROM mensagens_utilizador")

                        id_max = cur.fetchone()

                        if(id_max[0] == None):
                            novo_id = 1
                        else:
                            novo_id = int(id_max[0])+1


                        statement = """
                                        INSERT INTO mensagens_utilizador (mensagens, data_mensagem, lido, id, remetente, leilao_codigo_artigo, utilizador_username) 
                                                VALUES ( %s,   %s , %s, %s, %s,  %s ,   %s)"""

                        values = (mensagem, data, False, str(novo_id), remetente, leilaoID, row[0])

                        cur.execute(statement, values)
                
                result = 'Sucesso'
            else:
                result = 'Leilão já cancelado/encerrado'
                
        else:
            result = 'Apenas administradores podem cancelar leilões'

        cur.execute("commit")

    except (Exception, psycopg2.DatabaseError) as error:
        cur.execute("rollback")
        result = 'erro: ' + str(error)
    finally:
        if conn is not None:
            conn.close()
            cur.close()

    return result


## CANCELAR UM LEILAO
@app.route("/dbproj/cancelarleilao/<leilaoID>", methods=['PUT'])
def cancel_leilao(leilaoID):
    logger.info("###              CANCELAR LEILAO           ###");   

    logger.debug(f'leilaoID: {leilaoID}')

    try:
        token = request.form['token']

        user = authenticate_user_token(token)

        if user != 'erro: AuthError':
            if (check_ban(user) == False):
                result = cancelar_leilao(user, leilaoID) 
            else:
                return jsonify('Utilizador já banido')
        else: 
            return jsonify(user)

    except (Exception, psycopg2.DatabaseError) as error:
        result = 'erro: ' + str(error)

    return jsonify(result)
    

## ENCERRAR LEILAO
@app.route("/dbproj/endleilao", methods=['PUT'])
def end_leilao():
    logger.info("###              ENCERRAR LEILAO          ###");   

    conn = db_connection()
    cur = conn.cursor()

    data = datetime.datetime.now()

    try:
        cur.execute("BEGIN TRANSACTION")
        cur.execute("SELECT codigo_artigo, licitacao_atual FROM leilao WHERE data_hora_fim < %s and encerrado = %s", (data, False,))

        para_encerrar = cur.fetchall()

        if (para_encerrar != []):
            for row in para_encerrar:

                cur.execute("lock table leilao in exclusive mode")
                cur.execute("UPDATE leilao SET encerrado = %s WHERE codigo_artigo = %s", (True, row[0]))

                if (row[1] != None):
                    cur.execute("SELECT utilizador_username FROM licitacao WHERE valor = %s and leilao_codigo_artigo = %s and valida = %s", (row[1], row[0], True))
                    winner = cur.fetchone()

                    cur.execute("UPDATE leilao SET vencedor = %s WHERE codigo_artigo = %s", (winner, row[0]))

            result = 'Leilões encerrados'

        else:
            result = 'Sem leilões para encerrar'

        cur.execute("commit")

    except (Exception, psycopg2.DatabaseError) as error:
        result = 'erro: ' + str(error)
        cur.execute("rollback")
    finally:
        if conn is not None:
            conn.close()
            cur.close()

    return jsonify(result)


## BANIR UTILIZADOR
@app.route("/dbproj/banuser/<userID>", methods=['PUT'])
def ban_user(userID):
    logger.info("###              BANIR UTILIZADOR           ###");   

    logger.debug(f'userID: {userID}')

    conn = db_connection()
    cur = conn.cursor()
    

    try:
        token = request.form['token']

        user = authenticate_user_token(token)

        if user != 'erro: AuthError':
            if (check_ban(user) == False):

                cur.execute("BEGIN TRANSACTION")
                cur.execute("SELECT administrador FROM utilizador WHERE username LIKE %s", (user,))
                
                admin = cur.fetchone()

                if (admin[0] == True):

                    if (check_ban(userID) == False):
                        if (userID != user):
                            cur.execute("lock table utilizador in exclusive mode")
                            cur.execute("UPDATE utilizador SET banido = %s WHERE username LIKE %s", (True, userID,))
                            cur.execute("SELECT codigo_artigo FROM leilao WHERE utilizador_username LIKE %s", (userID,))

                            para_cancelar = cur.fetchall()

                            for row in para_cancelar:
                                res = cancelar_leilao(user, row[0])

                            cur.execute("SELECT id, leilao_codigo_artigo, valor FROM licitacao WHERE utilizador_username LIKE %s", (userID,))

                            para_cancelar = cur.fetchall()

                            for row in para_cancelar:
                                cur.execute("lock table licitacao in exclusive mode")
                                cur.execute("UPDATE licitacao SET valida = %s WHERE id = %s", (False, row[0]))

                            dicio_cancelado = {}
                            for id in para_cancelar:
                                if (id[1] in dicio_cancelado and id[2] > dicio_cancelado[id[1]][0]):
                                    dicio_cancelado[id[1]] = [id[2], id[0]]
                                elif (id[1] not in dicio_cancelado):
                                    dicio_cancelado[id[1]] = [id[2], id[0]]

                            for codigo in dicio_cancelado:
                                alterou = 0
                                cur.execute("SELECT leilao_codigo_artigo, valor FROM licitacao WHERE leilao_codigo_artigo LIKE %s and utilizador_username <> %s", (codigo, userID,))

                                dicio_a_cancelar = {}

                                res = cur.fetchall()

                                if res != []:
                                    for id in res:
                                        if (id[1] > dicio_cancelado[codigo][0]):
                                            if (id[0] in dicio_a_cancelar and id[1] > dicio_a_cancelar[codigo][0]):
                                                dicio_a_cancelar[codigo] = [id[1], id[0]]
                                            elif (id[0] not in dicio_a_cancelar):
                                                dicio_a_cancelar[codigo] = [id[1], id[0]]

                                    if (dicio_a_cancelar != {}):
                                        alterou = 1
                                        cur.execute("UPDATE licitacao SET valida = %s WHERE valor < %s and valor > %s", (False, dicio_a_cancelar[codigo][0], dicio_cancelado[codigo][0],))

                                        cur.execute("UPDATE licitacao SET valor = %s WHERE id = %s", (dicio_cancelado[codigo][0], dicio_a_cancelar[codigo][1],))

                                        cur.execute("UPDATE leilao SET licitacao_atual = %s WHERE codigo_artigo = %s", (dicio_cancelado[codigo][0], codigo,))

                                    else:
                                        for id in res:
                                            if (id[1] < dicio_cancelado[codigo][0]):
                                                if (id[0] in dicio_a_cancelar and id[1] > dicio_a_cancelar[codigo][0]):
                                                    dicio_a_cancelar[codigo] = [id[1], id[0]]
                                                elif (id[0] not in dicio_a_cancelar):
                                                    dicio_a_cancelar[codigo] = [id[1], id[0]]

                                        if (dicio_a_cancelar != {}):
                                            cur.execute("lock table leilao in exclusive mode")
                                            cur.execute("UPDATE leilao SET licitacao_atual = %s WHERE codigo_artigo = %s", (dicio_a_cancelar[codigo][0], dicio_a_cancelar[codigo][1],))
                                        else:
                                            cur.execute("lock table leilao in exclusive mode")
                                            cur.execute("UPDATE leilao SET licitacao_atual = %s WHERE codigo_artigo = %s", (None, codigo,))

                                else:
                                    cur.execute("lock table leilao in exclusive mode")
                                    cur.execute("UPDATE leilao SET licitacao_atual = %s WHERE codigo_artigo = %s", (None, codigo,))

                                if (alterou == 1):
                                        mensagem = 'Alteração de licitações no leilão ' + codigo + '. Pedimos desculpa pelo incómodo.'
                                        result = escrever_mensagem_leilao(codigo, user, mensagem, 'sim')

                            result = 'Sucesso'
                        else:
                            result = 'Um utilizador não se pode banir a si mesmo'
                    else:
                        result = 'Utilizador já banido/ não existe'
                else:
                    result = 'Apenas administradores podem banir utilizadores'
                
                cur.execute("commit")
            else:
                result = 'Administrador banido'
        else: 
            return jsonify(user)

    except (Exception, psycopg2.DatabaseError) as error:
        result = 'erro: ' + str(error)
        cur.execute("rollback")
    finally:
        if conn is not None:
            conn.close()
            cur.close()

    return jsonify(result)


## ESTATISTICAS
@app.route("/dbproj/estatisticasapp", methods=['GET'])
def get_estatisticas():
    logger.info("###              OBTER ESTATISTICAS          ###");   

    conn = db_connection()
    cur = conn.cursor()

    data = datetime.datetime.now()
    limite = data - datetime.timedelta(days=10)

    try:

        token = request.form['token']

        user = authenticate_user_token(token)

        if user != 'erro: AuthError':
            if (check_ban(user) == False):

                payload = []

                cur.execute("BEGIN TRANSACTION")
                cur.execute("SELECT administrador FROM utilizador WHERE username LIKE %s", (user,))
            
                admin = cur.fetchone()

                if (admin[0] == True):

                    statement = """
                                SELECT utilizador_username, COUNT(codigo_artigo)
                                FROM leilao
                                GROUP BY utilizador_username
                                ORDER BY COUNT(codigo_artigo) DESC
                                LIMIT 10  """

                    cur.execute(statement)

                    content = {'TOP 10': 'CRIADORES DE LEILAO'}

                    top_criadores = cur.fetchall()

                    if (top_criadores != []):
                        for i in range (len(top_criadores)):
                            ch = str(i+1)
                            va = top_criadores[i][0] + ' -> ' + str(top_criadores[i][1])
                            content[ch] = va

                    else:
                        content.update(Utilizadores = 'Não existem')

                    payload.append(content)

                    statement = """
                                SELECT vencedor, COUNT(codigo_artigo)
                                FROM leilao
                                GROUP BY vencedor
                                ORDER BY COUNT(codigo_artigo) DESC
                                LIMIT 10  """

                    cur.execute(statement)

                    content = {'TOP 10': 'VENCEDORES DE LEILAO'}

                    top_vencedores = cur.fetchall()

                    if (top_vencedores != []):
                        cont = 0
                        for i in range (len(top_vencedores)):
                            if (top_vencedores[i][0] != None):
                                cont +=1
                                ch = str(cont)
                                va = top_vencedores[i][0] + ' -> ' + str(top_vencedores[i][1])
                                content[ch] = va
                                
                    else:
                        content.update(Utilizadores = 'Não existem')

                    payload.append(content)

                    statement = """
                                SELECT leilao_codigo_artigo, min(data)
                                FROM historico
                                GROUP BY leilao_codigo_artigo
                                ORDER BY min(data)  """

                    cur.execute(statement)

                    leiloes_existentes = cur.fetchall()

                    cont = 0
                    if (leiloes_existentes != []):
                        for leil in leiloes_existentes:
                            if (leil[1] >= limite):
                                cont += 1
       
                    content = {'TOTAL DE LEILOES DOS ULTIMOS 10 DIAS': cont}
                    payload.append(content)

                else:
                   return jsonify('Apenas administradores podem ver as estatisticas')

                cur.execute("commit")
                
            else:
                return jsonify('Utilizador banido')
        else:
            return jsonify(user)

    except (Exception, psycopg2.DatabaseError) as error:
        resultado = 'erro: ' + str(error)
        cur.execute("rollback")
    finally:
        if conn is not None:
            conn.close()
            cur.close()

    return jsonify(payload)


## OBTER HISTORICO DE LEILAO
@app.route("/dbproj/historico/<leilaoID>", methods=['GET'])
def get_historico(leilaoID):
    logger.info("###              OBTER HISTORICO          ###");   

    logger.debug(f'leilaoID: {leilaoID}')

    conn = db_connection()
    cur = conn.cursor()

    try:
        token = request.form['token']

        user = authenticate_user_token(token)

        if user != 'erro: AuthError':
            if (check_ban(user) == False):
                cur.execute("BEGIN TRANSACTION")
                cur.execute("SELECT utilizador_username FROM leilao WHERE codigo_artigo = %s", (leilaoID,))

                payload = []

                rows = cur.fetchall()

                if (rows == []):
                    payload = 'Leilao nao encontrado'
                else:
                    cur.execute("SELECT leilao_codigo_artigo, data, titulo, descricao, detalhes_adicionais FROM historico WHERE leilao_codigo_artigo = %s", (leilaoID,))
                
                    rows = cur.fetchall()

                    for row in rows:
                        content={'id_licitacao' : row[0], 'valor_licitacao' : row[1], 'data_licitacao' : row[2], 'licitacao_valida' : row[3], 'username_licitacao' : row[4]}
                        payload.append(content)    

                cur.execute("commit")
                
            else:
                return jsonify('Utilizador banido')
        else:
            return jsonify(user)

    except (Exception, psycopg2.DatabaseError) as error:
        payload = 'erro: ' + str(error)
        cur.execute("rollback")
    finally:
        if conn is not None:
            conn.close()
            cur.close()

    return jsonify(payload)


## ACESSO À BASE DE DADOS
def db_connection():

    fich = open('api_configurations.txt', 'r')
    linhas = fich.readlines()
    for i in range(len(linhas)):
        linhas[i] = linhas[i].strip().split(':')

    us = linhas[0][1]
    ps = linhas[1][1]
    ht = linhas[2][1]
    pt = linhas[3][1]
    dtb = linhas[4][1]

    db = psycopg2.connect(user = us,
                            password = ps,
                            host = ht,
                            port = pt,
                            database = dtb)

    fich.close()

    return db


## MAIN
if __name__ == "__main__":

    # Set up the logging
    logging.basicConfig(filename="logs/log_file.log")
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s',
                              '%H:%M:%S')
                              # "%Y-%m-%d %H:%M:%S") # not using DATE to simplify
    ch.setFormatter(formatter)
    logger.addHandler(ch)


    time.sleep(1) # just to let the DB start before this print :-)


    logger.info("\n---------------------------------------------------------------\n" + 
                  "API v1.0 online: http://localhost:8080/dbproj/\n\n")


    

    app.run(host="0.0.0.0", port=8080, debug=True, threaded=True)



