import QtQuick 2.0
import calamares.slideshow 1.0

Presentation {
    id: presentation

    function nextSlide() {
        presentation.goToNextSlide()
    }

    Timer {
        interval: 12000
        running: presentation.activatedInCalamares
        repeat: true
        onTriggered: nextSlide()
    }

    Slide {
        Text {
            anchors.centerIn: parent
            width: presentation.width * 0.8
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            color: "#3DDC97"
            font.pixelSize: 28
            text: "Fray - NixOS gaming"
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 40
            width: presentation.width * 0.85
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            color: "#A8A29E"
            font.pixelSize: 16
            text: "Steam, Heroic, Faugus, GameMode, quatre bureaux."
        }
    }

    Slide {
        Text {
            anchors.centerIn: parent
            width: presentation.width * 0.8
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            color: "#FAFAF9"
            font.pixelSize: 26
            text: "Install via Calamares"
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 40
            width: presentation.width * 0.85
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            color: "#A8A29E"
            font.pixelSize: 16
            text: "Après reboot, clone le flake Fray et bascule avec fray-update --switch."
        }
    }
}
