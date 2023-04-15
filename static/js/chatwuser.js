function myFunc(vars) {
    return vars
}

$(document).ready(() => {
    $('#form_send_msg').on('submit', (e) => {
        e.preventDefault();
    });

    const socket = io();
    const room = "Chat " + parseInt(cur_chat_id);
    var data = data;
    var date_last = "";

    socket.on('connect', function () {
        socket.emit('join', { 'chat_name': room });
    });


    $('#message_input').on("click", function () {
        $.ajax({
            url: '/api/read_all_msgs/' + cur_chat_id
        }).done(function (res) {
            if (res['message'] == 'error') {
                console.log("ERROR");
            }
        });
    });

    socket.on('show_messages', function (data_msg) {
        for (let key of Object.keys(data_msg)) {
            if (key == Object.keys(data_msg).at(-1) || key == 0) {
                date_last = data_msg[key][3][0]
            }

            let author = data_msg[key][0];
            let msg = data_msg[key][1];
            let author_id = data_msg[key][2];

            let prev_date = date_last;
            date_last = data_msg[key][3][0];


            if (date_last != prev_date) {
                $('#messages').append(`<div class="text-muted align-self-center mb-4 mt-4">${date_last}</div>`);
            }

            if (author === 'Service message') {
                $('#messages').append(`<div class="text-muted align-self-center mb-4"><strong>${author}:</strong> ${msg}</div>`);

            } else {
                if (author_id == cur_user_id) {
                    $('#messages').append(
                        `<div style="max-width: 300px;" class="text-break border rounded-2 p-2 align-self-end mb-2">
                            <p class="flex-direction-column align-self-start m-0">${data_msg[key][1]}</p>
                            <div class="message_date mt-1 d-flex justify-content-end">
                                <p class="m-0 align-self-center">${data_msg[key][3][1]}</p>
                                <img class="mini-avatar ms-2" src="/userava/${author_id}">
                            </div>
                        </div>`);
                } else {
                    $('#messages').append(
                        `<div style="max-width: 300px;" class="text-break border rounded-2 p-2 align-self-start mb-2">
                            <p class="flex-direction-column align-self-start m-0">${data_msg[key][1]}</p>
                            <div class="message_date mt-1 d-flex justify-content-start">
                                <img class="mini-avatar me-2" src="/userava/${author_id}">
                                <p class="m-0 align-self-center">${data_msg[key][3][1]}</p>
                            </div>
                        </div>`);
                }

            }
        }

        // scroll the page after loading messages to input message field
        $('html, body').animate({ scrollTop: $("#msg_input").offset().top }, 100);
    });

    $('#send_msg').on('click', () => {
        socket.send({
            'msg': $('#message_input').val(),
            'user_id': cur_user_id,
            'chat_name': room
        });

        $.ajax({
            url: '/api/read_all_msgs/' + cur_chat_id
        }).done(function (res) {
            if (res['message'] == 'error') {
                console.log("ERROR");
            }
        });

        $('#message_input').val('');
    });

    socket.on('message', function (data) {
        if (data.msg.length > 0) {
            if (data.msg_date != date_last) {
                date_last = data.msg_date;
                $('#messages').append(`<div class="text-muted align-self-center mb-4">${date_last}</div>`);
            }

            if (data.user_id == cur_user_id) {
                $('#messages').append(
                    `<div style="max-width: 300px;" class="text-break border rounded-2 p-2 align-self-end mb-2">
                        <p class="flex-direction-column align-self-start m-0">${data.msg}</p>
                        <div class="message_date mt-1 d-flex justify-content-end">
                            <p class="m-0 align-self-center">${data.msg_time}</p>
                            <img class="mini-avatar ms-2" src="/userava/${data.user_id}">
                        </div>
                    </div>`);
            } else {
                $('#messages').append(
                    `<div style="max-width: 300px;" class="text-break border rounded-2 p-2 align-self-start mb-2">
                        <p class="flex-direction-column align-self-start m-0">${data.msg}</p>
                        <div class="message_date mt-1 d-flex justify-content-start">
                            <img class="mini-avatar me-2" src="/userava/${data.user_id}">
                            <p class="m-0 align-self-center">${data.msg_time}</p>
                        </div>
                    </div>`);
            }


        }
        // $('#messages').append(`<li><strong>${data.username}:</strong> ${data.msg}</li>`);
    });


});