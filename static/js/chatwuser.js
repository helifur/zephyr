function myFunc(vars) {
    return vars
}

$(document).ready(() => {
    $('#form_send_msg').on('submit', (e) => {
        e.preventDefault();
    });

    const socket = io();
    const username = "{{ user.name }}";
    var data = data;
    var cur_date = "";

    console.log($('#message_input').is(":focus"));

    $('#message_input').on("click", function () {
        var xmlHttp = new XMLHttpRequest();
        xmlHttp.open("GET", '/api/read_all_msgs/' + cur_chat_id, false); // false for synchronous request
        xmlHttp.send(null);
        console.log(xmlHttp.responseText);
        // return xmlHttp.responseText;
    });

    socket.on('show_messages', function (data_msg) {
        /* for (let index = 0; index < data_msg.length; index++) {
            if (data_msg[index][0] === 'Service message') {
                $('#messages').append(`<div class="text-muted"><strong>${data_msg[index][0]}:</strong> ${data_msg[index][1]}</div>`);
    
            } else {
                $('#messages').append(
                    `<div class="message"><strong>${data_msg[index][0]}:</strong> ${data_msg[index][1]}</li>`);
            }
    
        } */
        for (let key of Object.keys(data_msg)) {
            if (key == Object.keys(data_msg).at(-1)) {
                cur_date = data_msg[key][3][0]
            }

            let author = data_msg[key][0];
            let msg = data_msg[key][1];
            let author_id = data_msg[key][2];

            //console.log(data_msg);

            // if (data_msg[key]) {
            //     console.log(data_msg[key])
            // }

            if (author === 'Service message') {
                $('#messages').append(`<div class="text-muted align-self-center mb-4"><strong>${author}:</strong> ${msg}</div>`);

            } else {
                if (author_id == cur_user_id) {
                    $('#messages').append(
                        `<div class="mw-500 border rounded-2 p-2 align-self-end mb-2"><p class="flex-direction-column align-self-start m-0">${data_msg[key][1]}</p> <div class="message_date">${data_msg[key][3][1]}</div></div>`);
                } else {
                    $('#messages').append(
                        `<div class="mw-500 border rounded-2 p-2 align-self-start mb-2"><p class="flex-direction-column align-self-start m-0">${data_msg[key][1]}</p> <div class="message_date">${data_msg[key][3][1]}</div></div>`);
                }

            }
        }

    });

    $('#send_msg').on('click', () => {
        socket.send({
            'msg': $('#message_input').val(),
            'user_id': cur_user_id
        });

        $('#message_input').val('');
    });

    socket.on('message', function (data) {
        if (data.msg.length > 0) {
            if (data.msg_date != cur_date) {
                cur_date = data.msg_date;
                $('#messages').append(`<div class="text-muted align-self-center mb-4">${cur_date}</div>`);
            }

            if (data.user_id == cur_user_id) {
                $('#messages').append(
                    `<div class="mw-500 border rounded-2 p-2 align-self-end mb-2"><p class="flex-direction-column align-self-start m-0">${data.msg}</p> <div class="message_date">${data.msg_time}</div></div>`);
            } else {
                $('#messages').append(
                    `<div class="mw-500 border rounded-2 p-2 align-self-start mb-2"><p class="flex-direction-column align-self-start m-0">${data.msg}</p> <div class="message_date">${data.msg_time}</div></div>`);
            }


        }
        console.log('Received message');
        // $('#messages').append(`<li><strong>${data.username}:</strong> ${data.msg}</li>`);
    });


});