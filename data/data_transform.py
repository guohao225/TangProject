import sqlite3

conn_a = sqlite3.connect('./source.db')
cursor_a = conn_a.cursor()

# 连接到数据库 B
conn_b = sqlite3.connect('./source_all.db')
cursor_b = conn_b.cursor()

tangs = cursor_b.execute('SELECT * FROM alltangs').fetchall()
conn_b.close()

increase_id = 1
for row in tangs:
    row = row[1:len(row)-1]
    conn_a.execute("INSERT INTO alltangs(id, title,author, content,label,label_score,entitys, LC,MNLP,entity_MNLP,status,user_label,user_entitys,loop,selected) "
                   f"VALUES ({increase_id},?,?,?,?,?,?,?,?,?,?,?,?,?,?)", row)
    increase_id += 1

conn_a.commit()
conn_a.close()