private final class JerkgramTelemetry {
    static let shared = JerkgramTelemetry()
    private let queue = DispatchQueue(label: "org.jerkgram.telemetry", qos: .utility)
    private var activeTask: URLSessionDataTask?
    private var observer: NSObjectProtocol?
    private let endpoint = URL(string: "https://jerkgram-telemetry.cronusk1809.workers.dev/v1/activity")!
    private let secretKey = "jerkgram.telemetry.secret.v1"
    private let firstDateKey = "jerkgram.telemetry.firstDate.v1"
    private let receiptKey = "jerkgram.telemetry.installReceipt.v1"
    private let installReportedKey = "jerkgram.telemetry.installReported.v1"
    private let lastSuccessKey = "jerkgram.telemetry.lastSuccess.v1"
    private let minimumInterval: TimeInterval = 4 * 60 * 60
    private let lastAttemptAtKey = "jerkgram.telemetry.lastAttempt.v2"
    private let analyticsDayKey = "jerkgram.telemetry.opens.day"
    private let openCountTodayKey = "jerkgram.telemetry.opens.count"
    private let maximumOpenCount = 100000
    private var hasSeenActive = false
    private var enteredBackground = false
    private init() {
        observer = NotificationCenter.default.addObserver(forName: .jerkgramTelemetryPreferenceChanged, object: nil, queue: nil) { [weak self] _ in
            guard let self else { return }; self.queue.async { if !JerkgramTelemetryPreferences.isEnabled { self.activeTask?.cancel(); self.activeTask = nil } }
        }
    }
    func applicationDidBecomeActive() {
        let shouldCountOpen = !self.hasSeenActive || self.enteredBackground
        self.hasSeenActive = true
        self.enteredBackground = false
        guard JerkgramTelemetryPreferences.isEnabled else { return }
        guard shouldCountOpen else { return }
        queue.async { [weak self] in
            guard let self else { return }
            guard JerkgramTelemetryPreferences.isEnabled else { return }
            self.recordOpen()
            self.submitIfNeeded()
        }
    }
    func applicationDidEnterBackground() {
        self.enteredBackground = true
    }
    private func analyticsDayString(_ date: Date) -> String {
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = TimeZone(identifier: "Europe/Moscow") ?? TimeZone(secondsFromGMT: 3 * 60 * 60)!
        let components = calendar.dateComponents([.year, .month, .day], from: date)
        return String(
            format: "%04d-%02d-%02d",
            components.year ?? 0,
            components.month ?? 0,
            components.day ?? 0
        )
    }

    private func recordOpen() {
        let defaults = UserDefaults.standard
        let analyticsDay = self.analyticsDayString(Date())
        let previousDay = defaults.string(forKey: self.analyticsDayKey)
        let previousCount = previousDay == analyticsDay ? defaults.integer(forKey: self.openCountTodayKey) : 0
        defaults.set(analyticsDay, forKey: self.analyticsDayKey)
        defaults.set(min(self.maximumOpenCount, max(0, previousCount) + 1), forKey: self.openCountTodayKey)
    }

    private func submitIfNeeded() {
        guard JerkgramTelemetryPreferences.isEnabled else { return }
        let defaults = UserDefaults.standard; let now = Date()
        if let last = defaults.object(forKey: lastAttemptAtKey) as? Date, now.timeIntervalSince(last) < minimumInterval { return }
        guard activeTask == nil else { return }
        let secret = localSecret(defaults: defaults)
        let analyticsDay=analyticsDayString(now)
        let analyticsDayId=hmac(secret,"jerkgram-msk-day-v1:"+analyticsDay)
        let openCountToday=max(1,defaults.integer(forKey:openCountTodayKey))
        let firstDate: Date
        if let stored = defaults.object(forKey: firstDateKey) as? Date { firstDate = stored } else { firstDate = now; defaults.set(now, forKey: firstDateKey) }
        var c = Calendar(identifier: .iso8601); c.timeZone = TimeZone(secondsFromGMT: 0)!
        let year=c.component(.year,from:now), month=c.component(.month,from:now), day=c.component(.day,from:now)
        let weekYear=c.component(.yearForWeekOfYear,from:now), week=c.component(.weekOfYear,from:now)
        let dayId=hmac(secret,String(format:"%04d-%02d-%02d",year,month,day))
        let weekId=hmac(secret,String(format:"%04d-W%02d",weekYear,week))
        let monthId=hmac(secret,String(format:"%04d-%02d",year,month))
        let receipt: String
        if let existing=defaults.string(forKey:receiptKey){receipt=existing}else{receipt=randomBytes(16).map{String(format:"%02x",$0)}.joined();defaults.set(receipt,forKey:receiptKey)}
        let version=JerkgramReleaseIdentity.technicalVersion
        let build=JerkgramReleaseIdentity.build
        let os=UIDevice.current.systemVersion; let major=Int(os.split(separator:".").first ?? "0") ?? 0
        let region=Locale.current.regionCode ?? "ZZ"
        let age=max(0,c.dateComponents([.day],from:c.startOfDay(for:firstDate),to:c.startOfDay(for:now)).day ?? 0)
        let model=hardwareModel()
        var payload:[String:Any]=["schema":1,"appVersion":version,"build":build,"iosVersion":os,"iosMajor":major,"deviceRegion":region,"deviceModel":model,"installAgeDays":age,"dayId":dayId,"weekId":weekId,"monthId":monthId,"event":"app_active","ts":Int(now.timeIntervalSince1970),"analyticsDay":analyticsDay,"analyticsDayId":analyticsDayId,"openCountToday":openCountToday]
        if !defaults.bool(forKey:installReportedKey){payload["installReceiptId"]=receipt}
        guard let body=try? JSONSerialization.data(withJSONObject:payload) else{return}
        var request=URLRequest(url:endpoint);request.httpMethod="POST";request.httpBody=body;request.timeoutInterval=8.0;request.setValue("application/json",forHTTPHeaderField:"Content-Type")
        guard JerkgramTelemetryPreferences.isEnabled else{return}
        defaults.set(now,forKey:lastAttemptAtKey)
        let task = URLSession.shared.dataTask(with: request) { [weak self] _, response, error in
            guard let self else { return }
            self.queue.async {
                defer { self.activeTask = nil }
                guard JerkgramTelemetryPreferences.isEnabled else { return }
                if let error = error as NSError? {
                    Logger.shared.log("JerkgramTelemetry", "transport failure code=\(error.code)")
                }
                guard let http = response as? HTTPURLResponse else {
                    Logger.shared.log("JerkgramTelemetry", "missing HTTP response")
                    return
                }
                Logger.shared.log("JerkgramTelemetry", "activity HTTP status=\(http.statusCode)")
                guard (200..<300).contains(http.statusCode) else { return }
                defaults.set(Date(), forKey: self.lastSuccessKey)
                if !defaults.bool(forKey: self.installReportedKey) {
                    defaults.set(true, forKey: self.installReportedKey)
                    defaults.removeObject(forKey: self.receiptKey)
                }
            }
        }
        activeTask=task;task.resume()
    }
    private func hardwareModel()->String {
        var info=utsname()
        guard uname(&info) == 0 else { return "unknown" }
        let capacity=MemoryLayout.size(ofValue:info.machine)
        return withUnsafePointer(to:&info.machine) { pointer in
            pointer.withMemoryRebound(to:CChar.self,capacity:capacity) { String(cString:$0) }
        }
    }
    private func localSecret(defaults:UserDefaults)->[UInt8]{if let data=defaults.data(forKey:secretKey),data.count==32{return Array(data)};let bytes=randomBytes(32);defaults.set(Data(bytes),forKey:secretKey);return bytes}
    private func randomBytes(_ count:Int)->[UInt8]{var generator=SystemRandomNumberGenerator();return(0..<count).map{_ in UInt8.random(in:UInt8.min...UInt8.max,using:&generator)}}
    private func hmac(_ key:[UInt8],_ value:String)->String{let block=64;var k=key;if k.count>block{k=sha256(k)};if k.count<block{k += [UInt8](repeating:0,count:block-k.count)};let inner=sha256(zip(k,[UInt8](repeating:0x36,count:block)).map{$0.0 ^ $0.1}+Array(value.utf8));let out=sha256(zip(k,[UInt8](repeating:0x5c,count:block)).map{$0.0 ^ $0.1}+inner);return out.map{String(format:"%02x",$0)}.joined()}
    private func sha256(_ input:[UInt8])->[UInt8]{let constants:[UInt32]=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];var m=input;let bits=UInt64(m.count)*8;m.append(0x80);while m.count%64 != 56{m.append(0)};for s in stride(from:56,through:0,by:-8){m.append(UInt8((bits>>UInt64(s))&0xff))};var h:[UInt32]=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];for off in stride(from:0,to:m.count,by:64){var w=[UInt32](repeating:0,count:64);for i in 0..<16{let j=off+i*4;w[i]=UInt32(m[j])<<24|UInt32(m[j+1])<<16|UInt32(m[j+2])<<8|UInt32(m[j+3])};for i in 16..<64{let a=w[i-15],b=w[i-2];let s0=(a>>7|a<<25)^(a>>18|a<<14)^(a>>3);let s1=(b>>17|b<<15)^(b>>19|b<<13)^(b>>10);w[i]=w[i-16]&+s0&+w[i-7]&+s1};var a=h[0],b=h[1],c=h[2],d=h[3],e=h[4],f=h[5],g=h[6],x=h[7];for i in 0..<64{let s1=(e>>6|e<<26)^(e>>11|e<<21)^(e>>25|e<<7);let ch=(e&f)^((~e)&g);let t1=x&+s1&+ch&+constants[i]&+w[i];let s0=(a>>2|a<<30)^(a>>13|a<<19)^(a>>22|a<<10);let maj=(a&b)^(a&c)^(b&c);let t2=s0&+maj;x=g;g=f;f=e;e=d&+t1;d=c;c=b;b=a;a=t1&+t2};for i in 0..<8{h[i]=h[i]&+[a,b,c,d,e,f,g,x][i]}};return h.flatMap{v in[UInt8(v>>24),UInt8((v>>16)&255),UInt8((v>>8)&255),UInt8(v&255)]}}
}

class IntegrationFixture {
    func launch() {
        JerkGramLegacyDefaultsMigration.run()
    }
    func handleDidBecomeActive() {
    }
    func handleDidEnterBackground() {
    }
    func handleWillResignActive() {
    }
}
