const pg = require('pg');
const pool = new pg.Pool();

module.exports.newkey = function(name, hash, public_key){
    query = "INSERT INTO keys (name, hash, public_key) VALUES ('" + name + "', '" + hash + "', '" + public_key + "');"
    
    return new Promise((suc, rej) => {
        pool.query(query, (err, res) => {
                if (err){
                    if (err.code == '23505')
                        rej("Duplicated key");
                    else{
                        console.log("DATABASE ERROR");
                        rej("Database error");
                    }
                }else
                    suc();
            }
        );
    });
}

module.exports.newtransaction = function(transaction){
    var query = "INSERT INTO transactions (hash, type, mode, transmitter, receiver, client_timestamp, transaction_data, sign) \
    VALUES ('" + transaction.hash + "', " + transaction.type + ", " + transaction.mode + ", '" + transaction.transmitter + "', ";
    if (transaction.receiver){
        query += "'" + transaction.receiver + "', ";
    }else{
        query += "NULL, ";
    }
    query += "to_timestamp(" + transaction.timestamp + "), '" + JSON.stringify(transaction.data, null, 0) + "', '" + transaction.sign + "');"
    
    return new Promise((suc, rej) => {
        pool.query(query, (err, res) => {
                if (err){
                    if (err.code != '23505') //Si la transacción está repetida, no hace nada
                        console.log("DATABASE ERROR");
                }else
                    suc();
            }
        );
    });
}

module.exports.getpk = function(key_hash){
    query = "SELECT public_key FROM keys WHERE hash = '" + key_hash + "' AND active = true;"
    return new Promise((suc, rej) => {
        pool.query(query, (err, res) => {
            if (err){
                console.log("DATABASE ERROR");
                rej("Database error.")
            }else if (res.rowCount == 0)
                rej("The key doesn't exist")
            else
                suc(res.rows[0].public_key);
        });
    });
}

module.exports.new_available_inputs = function(key, product, inputs){
    query = "INSERT INTO available_inputs (key_hash, product, inputs) VALUES ('" + key + "', '" + product + "', ARRAY[";
    for(i = 0; i < inputs.length; i++){
        if (i != 0)
            query += ", ";
        query += "'" + JSON.stringify(inputs[i], null, 0) + "'";
    }
    query += "]::json[]);"
    pool.query(query, (err, res) => {
            if (err){
                console.log("DATABASE ERROR");
            }
        }
    );
}

module.exports.del_available_inputs = function(key, product){
    query = "DELETE FROM available_inputs WHERE key_hash = '" + key + "' AND product = '" + product + "';";
    pool.query(query, (err, res) => {
            if (err){
                console.log("DATABASE ERROR");
            }
        }
    );
}

module.exports.get_available_inputs = function(key, product){
    query = "SELECT inputs FROM available_inputs WHERE key_hash = '" + key + "' AND product = '" + product + "';";
    return new Promise((suc, rej) => {
        pool.query(query, (err, res) => {
            if (err)
                console.log("DATABASE ERROR");
            else if (res.rowCount == 0)
                suc(null);
            else
                suc(res.rows[0].inputs);
        });
    });
}

module.exports.update_available_inputs = function(key, product, inputs){
    query = "UPDATE available_inputs SET inputs = ARRAY[";
    for(i = 0; i < inputs.length; i++){
        if (i != 0)
            query += ", ";
        query += "'" + JSON.stringify(inputs[i], null, 0) + "'";
    }
    query += "]::json[] WHERE key_hash = '" + key + "' AND product = '" + product + "';";
    pool.query(query, (err, res) => {
            if (err){
                console.log("DATABASE ERROR");
            }
        }
    );
}