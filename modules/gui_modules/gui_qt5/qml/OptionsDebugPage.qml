//OptionsDebugPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"
import "backend"

BasePage {
    id: debugPage
    headerText : "Debug"

    property alias logFileEnabled: logFileEnabledProp.value
    OptProp {id: logFileEnabledProp; key : "loggingStatus"; value : false}

    property alias logFileCompression: logFileCompressionProp.value
    OptProp {id: logFileCompressionProp; key : "compressLogFile"; value : false}

    property string logFilePath : setLogFilePath()

    function setLogFilePath() {
        rWin.python.call("modrana.gui.log_manager.get_log_file_path", [], function(v){
            if (v) {
                debugPage.logFilePath = v
            } else {
                debugPage.logFilePath = qsTr("log file disabled")
            }
    })
        return qsTr("log path unknown")
   }

    content : ContentColumn {
        TextSwitch {
            text : qsTr("Show debug button")
            checked : rWin.showDebugButton
            onCheckedChanged : {
                 rWin.showDebugButton = checked
            }
        }
        TextSwitch {
            text : qsTr("Show unfinished features")
            checked : rWin.showUnfinishedFeatures
            onCheckedChanged : {
                rWin.showUnfinishedFeatures = checked
            }
        }
        TextSwitch {
            text : qsTr("Tile display debugging")
            checked : rWin.tileDebug
            onCheckedChanged : {
                rWin.tileDebug = checked
            }
        }
        TextSwitch {
            text : qsTr("Tile storage debugging")
            checked : rWin.tileStorageDebug
            onCheckedChanged : {
                rWin.tileStorageDebug = checked
            }
        }
        TextSwitch {
            text : qsTr("Location debugging")
            checked : rWin.locationDebug
            onCheckedChanged : {
                rWin.locationDebug = checked
            }
        }
        Label {
            text : "Logging"
        }
        TextSwitch {
            text : qsTr("Log file")
            checked : logFileEnabled
            onCheckedChanged : {
                logFileEnabled = checked
            }
        }
        TextSwitch {
            text : qsTr("Log file compression")
            checked : logFileCompression
            onCheckedChanged : {
                logFileCompression = checked
            }
        }
        Label {
            text : debugPage.logFilePath
            wrapMode : Text.WrapAnywhere
            width : parent.width
        }
        Label {
            text : "Notifications"
        }
        Button {
            text : "Notify"
            onClicked : {
                rWin.notify("Hello world!")
            }
        }
        Button {
            text : "Notify long"
            onClicked : {
                rWin.notify("ModRana is a flexible navigation software for (not only) mobile Linux devices.")
            }
        }
    }
}
