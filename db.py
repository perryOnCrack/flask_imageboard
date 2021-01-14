import mariadb
import sys

def connect():
    # Instantiate Connection
    try:
        conn = mariadb.connect(
            user="db_final_user",
            password="",
            host="localhost",
            port=3306)
        return [True, conn]

    except mariadb.Error as e:
        return [False, f"Error connecting to MariaDB Platform: {e}"]


def get_index_data():
    conn = connect()
    if conn[0]:
        ret = {}
        conn = conn[1]
        cur = conn.cursor()
        cur.execute('SELECT name, id FROM 5chan.boards')
        for (name, id) in cur:
            ret[id] = name
        conn.close()
        return [True, ret]
    else:
        return conn


def get_board_data(b_id, page): # Tasty spaghetti.
    conn = connect()
    if conn[0]:
        try:
            ret = {}
            # {'title': '', 'list': [{'t_id': '', 'head': {'c_id': '', 'time': '', 'text': '', 'image': '', r_to: ''}, 'last': {'c_id': '', 'time': '', 'text': '', 'image': '', 'r_to': ''}, 'time': }, ...] }
            conn = conn[1]
            cur = conn.cursor()
            # Get board title.
            cur.execute('SELECT name FROM 5chan.boards WHERE id = ?', (b_id,))
            for (name,) in cur:
                ret['title'] = name

            # Get thread id list.
            ret['list'] = []
            cur.execute('SELECT id, head, last, time FROM 5chan.threads WHERE b_id = ? ORDER BY time DESC LIMIT ?, 10', (b_id, (int(page)-1)*10,))
            for (id, head, last, time) in cur:
                ret['list'].append({'t_id': id, 'head': head, 'last': last, 'time': time})
            print(ret)

            # Get each threads' first and last comments.
            for thread in ret['list']:
                head_data = get_comment(thread['head'])
                if head_data[0]:
                    thread['head'] = head_data[1]
                else:
                    return head_data

                last_data = get_comment(thread['last'])
                if last_data[0]:
                    thread['last'] = last_data[1]
                else:
                    return last_data

            conn.close()
            return [True, ret]
        
        except mariadb.Error as e:
            return [False, f"Error connecting to MariaDB Platform: {e}"]
    else:
        return conn

def get_comment(c_id):
    c_id = str(c_id).lower()
    conn = connect()
    if conn[0]:
        ret = {}
        # {'c_id': '', 'time': '', 'text': '', 'image': '', r_to: '', 'c_index': }
        conn = conn[1]
        cur = conn.cursor()
        try:
            cur.execute('SELECT time, text, image, replyto, c_index FROM 5chan.comments WHERE id = ?', (c_id,))
            for (time, text, image, replyto, c_index) in cur:
                ret = {'c_id': c_id, 'time': time, 'text': text, 'image': image, 'r_to': replyto, 'c_index': c_index}
        except mariadb.Error as e:
            return [False, f"Error connecting to MariaDB Platform: {e}"]        
        conn.close()
        return [True, ret]
    else:
        return conn


def get_thread_data(b_id, t_id):
    conn = connect()
    t_id = str(t_id).lower()
    b_id = str(b_id).lower()
    if conn[0]:
        ret = []
        conn = conn[1]
        cur = conn.cursor()
        # Get comment id list
        c_id_list = []
        cur.execute('SELECT id FROM 5chan.comments WHERE t_id = ? ORDER BY c_index', (t_id,))
        for (id,) in cur:
            c_id_list.append(id)
        c_list = []
        for id in c_id_list:
            result = get_comment(id)
            if not result[0]:
                return result
            c_list.append(result[1])
        #print(c_list)
        return [True, c_list]
    else:
        return conn
    


def set_comment(b_id, t_id, comment=None, image=None, re=None):
    conn = connect()
    t_id = str(t_id).lower()
    if conn[0]:
        ret = []
        conn = conn[1]
        cur = conn.cursor()
        if t_id == 'new':
            try:
                # Insert a new thread
                cur.execute('INSERT INTO 5chan.threads(b_id) VALUES (?) RETURNING id', (b_id,))
                new_t_id = None
                for (id,) in cur:
                    new_t_id = id
                #print(new_t_id)
                #print(type(new_t_id))

                # Insert a new comment (c_index = 0)
                cur.execute('INSERT INTO 5chan.comments(t_id, text, image, replyto) VALUES (?, ?, ?, ?) RETURNING id', (new_t_id, comment, image, re))
                new_c_id = None
                for (id,) in cur:
                    new_c_id = id
                #print(new_c_id)
                #print(type(new_c_id))

                # Update the thread's head and last
                cur.execute('UPDATE 5chan.threads SET head = ?, last = ? WHERE id = ?', (new_c_id, new_c_id, new_t_id))

                # Finalize return value.
                ret = [True, new_t_id]
                conn.commit()

            except mariadb.Error as e:
                ret = [False, f"Error: {e}"]
        else:
            try:
                # Get the thread's last comment id
                cur.execute('SELECT last FROM 5chan.threads WHERE id = ?', (t_id,))
                last_c_id = None
                for (last,) in cur:
                    last_c_id = last
                
                # Get last comment's c_index
                cur.execute('SELECT c_index FROM 5chan.comments WHERE id = ?', (last_c_id,))
                last_c_index = None
                for (c_index,) in cur:
                    last_c_index = c_index
                
                # Insert a new comment (last c_index + 1)
                cur.execute('INSERT INTO 5chan.comments(t_id, text, image, replyto, c_index) VALUES (?, ?, ?, ?, ?) RETURNING id', (t_id, comment, image, re, last_c_index+1))
                new_c_id = None
                for (id,) in cur:
                    new_c_id = id

                # Update the thread's last
                cur.execute('UPDATE 5chan.threads SET last = ? WHERE id = ?', (new_c_id, t_id))

                # Finalize return value.
                ret = [True, t_id]
                conn.commit()

            except mariadb.Error as e:
                ret = [False, f"Error: {e}"]
            
            except Exception as e:
                ret = [False, f'ERR:{e}']
        
        conn.close()
        return ret
    else:
        return conn


if __name__ == "__main__":
    #print(set_comment('b', 'new', 'yah, new thread'))
    #print(set_comment('b', '999', 'shouldn\'t work'))
    #print(get_comment(15))
    #print(get_board_data('v', 1))
    #get_thread_data('v', 40)
    set_comment('v', 50, '2123132')