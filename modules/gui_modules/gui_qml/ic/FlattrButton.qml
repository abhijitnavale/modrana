//FlattrButton.qml

import QtQuick 1.1


Rectangle {
    id : flattrButton
    color : flattrMA.pressed ? "limegreen" : "green"
    radius : 5
    width : 210
    height : 45
    property string url : ""

    Text {
        anchors.horizontalCenter : parent.horizontalCenter
        anchors.verticalCenter : parent.verticalCenter
        text : "<h3>Flattr this !</h3>"
        color : "white"
    }
    MouseArea {
        id : flattrMA
        anchors.fill : parent
        onClicked : {
            console.log('Flattr button clicked')
            Qt.openUrlExternally(url)
        }
    }
}

