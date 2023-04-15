$('document').ready(function () {
    $('#update_chats').click(fetchChats);

    function fetchChats() {
        // URL на который будем отправлять GET запрос
        const requestURL = '/api/check_chats';
        const xhr = new XMLHttpRequest();
        xhr.open('GET', requestURL);
        xhr.onload = () => {
            if (xhr.status !== 200) {
                return;
            }

            var data = JSON.parse(xhr.response);

            if (xhr.response.length > 0) {
                for (let key of Object.keys(data)) {
                    console.log(key);
                    if ($('#chat_head_1').text().includes('Новое')) {
                        // pass
                    } else {
                        $('#chat_head_' + key).html(data[key] + ' <span class="badge rounded-pill text-bg-danger">Новое</span>');
                    }

                }
            }


        }
        xhr.send();
    }

});