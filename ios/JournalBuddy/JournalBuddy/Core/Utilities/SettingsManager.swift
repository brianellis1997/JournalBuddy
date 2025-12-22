import Foundation

class SettingsManager: ObservableObject {
    static let shared = SettingsManager()

    private let defaults = UserDefaults.standard

    private enum Keys {
        static let selectedVoiceId = "selectedVoiceId"
        static let selectedVoiceName = "selectedVoiceName"
    }

    @Published var selectedVoice: Voice? {
        didSet {
            if let voice = selectedVoice {
                defaults.set(voice.id, forKey: Keys.selectedVoiceId)
                defaults.set(voice.name, forKey: Keys.selectedVoiceName)
            } else {
                defaults.removeObject(forKey: Keys.selectedVoiceId)
                defaults.removeObject(forKey: Keys.selectedVoiceName)
            }
        }
    }

    private init() {
        if let id = defaults.string(forKey: Keys.selectedVoiceId),
           let name = defaults.string(forKey: Keys.selectedVoiceName) {
            self.selectedVoice = Voice(id: id, name: name)
        }
    }

    var selectedVoiceId: String? {
        selectedVoice?.id
    }
}
