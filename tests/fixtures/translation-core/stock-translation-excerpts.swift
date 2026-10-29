// Exact Official13.1.1 fb0e62ba8a147f0821da6aa63c09da7d79a10111 owner excerpts.
func _internal_translateTexts(network: Network, texts: [(String, [MessageTextEntity])], toLang: String, tone: TranslationTone = .neutral) -> Signal<[(String, [MessageTextEntity])], TranslationError> {
    var flags: Int32 = 0
    flags |= (1 << 1)
    
    if tone != .neutral {
        flags |= (1 << 2)
    }
    
    var apiTexts: [Api.TextWithEntities] = []
    for text in texts {
        apiTexts.append(.textWithEntities(.init(text: text.0, entities: apiEntitiesFromMessageTextEntities(text.1, associatedPeers: SimpleDictionary()))))
    }

    return network.request(Api.functions.messages.translateText(flags: flags, peer: nil, id: nil, text: apiTexts, toLang: toLang, tone: tone.rawValue))
    |> mapError { error -> TranslationError in
        if error.errorDescription.hasPrefix("FLOOD_WAIT") {
            return .limitExceeded
        } else if error.errorDescription == "MSG_ID_INVALID" {
            return .invalidMessageId
        } else if error.errorDescription == "INPUT_TEXT_EMPTY" {
            return .textIsEmpty
        } else if error.errorDescription == "INPUT_TEXT_TOO_LONG" {
            return .textTooLong
        } else if error.errorDescription == "TO_LANG_INVALID" {
            return .invalidLanguage
        } else {
            return .generic
        }
    }
    |> mapToSignal { result -> Signal<[(String, [MessageTextEntity])], TranslationError> in
        var texts: [(String, [MessageTextEntity])] = []
        switch result {
        case let .translateResult(translateResultData):
            let results = translateResultData.result
            for result in results {
                if case let .textWithEntities(textWithEntitiesData) = result {
                    let (text, entities) = (textWithEntitiesData.text, textWithEntitiesData.entities)
                    texts.append((text, messageTextEntitiesFromApiEntities(entities)))
                }
            }
        }
        return .single(texts)
    }
}

func _internal_translateMessages(
func _internal_translateMessagesByPeerId(account: Account, peerId: EnginePeer.Id, messageIds: [EngineMessage.Id], fromLang: String?, toLang: String, enableLocalIfPossible: Bool, tone: TranslationTone = .neutral) -> Signal<Void, TranslationError> {
    return account.postbox.transaction { transaction -> (Api.InputPeer?, [Message]) in
        return (transaction.getPeer(peerId).flatMap(apiInputPeer), messageIds.compactMap({ transaction.getMessage($0) }))
    }
    |> castError(TranslationError.self)
    |> mapToSignal { (inputPeer, messages) -> Signal<Void, TranslationError> in
        guard let inputPeer = inputPeer else {
            return .never()
        }
        
        let polls = messages.compactMap { message in
            if let poll = message.media.first as? TelegramMediaPoll {
                return (poll, message.id)
            } else {
                return nil
            }
        }
        let pollSignals = polls.map { (poll, id) in
            var texts: [(String, [MessageTextEntity])] = []
            texts.append((poll.text, poll.textEntities))
            for option in poll.options {
                texts.append((option.text, option.entities))
            }
            if let solution = poll.results.solution {
                texts.append((solution.text, solution.entities))
            }
            return _internal_translateTexts(network: account.network, texts: texts, toLang: toLang)
        }
        
        let audioTranscriptions = messages.compactMap { message in
            if let audioTranscription = message.attributes.first(where: { $0 is AudioTranscriptionMessageAttribute }) as? AudioTranscriptionMessageAttribute, !audioTranscription.text.isEmpty && !audioTranscription.isPending {
                return (audioTranscription.text, message.id)
            } else {
                return nil
            }
        }
        let audioTranscriptionsSignals = audioTranscriptions.map { (text, id) in
            return _internal_translate(network: account.network, text: text, toLang: toLang)
        }
        
        var flags: Int32 = 0
        flags |= (1 << 0)
        if tone != .neutral {
            flags |= (1 << 2)
        }

        // Rich messages (a `RichTextMessageAttribute`) translate through `messages.translateRichMessage`
        // (per the layer-228 contract: pick translateText vs translateRichMessage by message type).
        let richMessageIds = messages.filter { $0.attributes.contains(where: { $0 is RichTextMessageAttribute }) }.map { $0.id }
        let plainMessageIds = messageIds.filter { !richMessageIds.contains($0) }

        let richSignal: Signal<Void, TranslationError>
        if richMessageIds.isEmpty {
            richSignal = .single(Void())
        } else {
            richSignal = _internal_translateRichMessages(account: account, inputPeer: inputPeer, messageIds: richMessageIds, toLang: toLang, tone: tone)
            |> map { _ in Void() }
        }

        let id: [Int32] = plainMessageIds.map { $0.id }

        let msgs: Signal<Api.messages.TranslatedText?, TranslationError>
        if id.isEmpty {
            msgs = .single(nil)
        } else {
            if enableLocalIfPossible, let engineExperimentalInternalTranslationService, let fromLang {
                msgs = account.postbox.transaction { transaction -> [MessageId: String] in
                    var texts: [MessageId: String] = [:]
                    for messageId in plainMessageIds {
                        if let message = transaction.getMessage(messageId) {
                            texts[message.id] = message.text
                        }
                    }
                    return texts
                }
                |> castError(TranslationError.self)
                |> mapToSignal { messageTexts -> Signal<Api.messages.TranslatedText?, TranslationError> in
                    var mappedTexts: [AnyHashable: String] = [:]
                    for (id, text) in messageTexts {
                        mappedTexts[AnyHashable(id)] = text
                    }
                    return engineExperimentalInternalTranslationService.translate(texts: mappedTexts, fromLang: fromLang, toLang: toLang)
                    |> castError(TranslationError.self)
                    |> mapToSignal { resultTexts -> Signal<Api.messages.TranslatedText?, TranslationError> in
                        guard let resultTexts else {
                            return .fail(.generic)
                        }
                        var result: [Api.TextWithEntities] = []
                        for messageId in plainMessageIds {
                            if let text = resultTexts[AnyHashable(messageId)] {
                                result.append(.textWithEntities(.init(text: text, entities: [])))
                            } else if let text = messageTexts[messageId] {
                                result.append(.textWithEntities(.init(text: text, entities: [])))
                            } else {
                                result.append(.textWithEntities(.init(text: "", entities: [])))
                            }
                        }
                        return .single(.translateResult(.init(result: result)))
                    }
                }
            } else {
                msgs = account.network.request(Api.functions.messages.translateText(flags: flags, peer: inputPeer, id: id, text: nil, toLang: toLang, tone: tone != .neutral ? tone.rawValue : nil))
                |> map(Optional.init)
                |> mapError { error -> TranslationError in
                    if error.errorDescription.hasPrefix("FLOOD_WAIT") {
                        return .limitExceeded
                    } else if error.errorDescription == "MSG_ID_INVALID" {
                        return .invalidMessageId
                    } else if error.errorDescription == "INPUT_TEXT_EMPTY" {
                        return .textIsEmpty
                    } else if error.errorDescription == "INPUT_TEXT_TOO_LONG" {
                        return .textTooLong
                    } else if error.errorDescription == "TO_LANG_INVALID" {
                        return .invalidLanguage
                    } else {
                        return .generic
                    }
                }
            }
        }
        
        return combineLatest(msgs, richSignal, combineLatest(pollSignals), combineLatest(audioTranscriptionsSignals))
        |> mapToSignal { (result, _, pollResults, audioTranscriptionsResults) -> Signal<Void, TranslationError> in
            return account.postbox.transaction { transaction in
                if case let .translateResult(translateResultData) = result {
                    let results = translateResultData.result
                    var index = 0
                    for result in results {
                        guard index < plainMessageIds.count else { break }
                        let messageId = plainMessageIds[index]
                        if case let .textWithEntities(textWithEntitiesData) = result {
                            let (text, entities) = (textWithEntitiesData.text, textWithEntitiesData.entities)
                            let updatedAttribute: TranslationMessageAttribute = TranslationMessageAttribute(text: text, entities: messageTextEntitiesFromApiEntities(entities), toLang: toLang)
                            transaction.updateMessage(messageId, update: { currentMessage in
                                let storeForwardInfo = currentMessage.forwardInfo.flatMap(StoreMessageForwardInfo.init)
                                var attributes = currentMessage.attributes.filter { !($0 is TranslationMessageAttribute) }
                                
                                attributes.append(updatedAttribute)
                                
                                return .update(StoreMessage(id: currentMessage.id, customStableId: nil, globallyUniqueId: currentMessage.globallyUniqueId, groupingKey: currentMessage.groupingKey, threadId: currentMessage.threadId, timestamp: currentMessage.timestamp, flags: StoreMessageFlags(currentMessage.flags), tags: currentMessage.tags, globalTags: currentMessage.globalTags, localTags: currentMessage.localTags, forwardInfo: storeForwardInfo, authorId: currentMessage.author?.id, text: currentMessage.text, attributes: attributes, media: currentMessage.media))
                            })
                        }
                        index += 1
                    }
                }
                
                if !pollResults.isEmpty {
                    for (i, poll) in polls.enumerated() {
                        let result = pollResults[i]
                        if !result.isEmpty {
                            transaction.updateMessage(poll.1, update: { currentMessage in
                                let storeForwardInfo = currentMessage.forwardInfo.flatMap(StoreMessageForwardInfo.init)
                                var attributes = currentMessage.attributes.filter { !($0 is TranslationMessageAttribute) }
                                var attrOptions: [TranslationMessageAttribute.Additional] = []
                                for (i, _) in poll.0.options.enumerated() {
                                    var translated = result.count > i + 1 ? result[i + 1] : (poll.0.options[i].text, poll.0.options[i].entities)
                                    if translated.0.isEmpty {
                                        translated = (poll.0.options[i].text, poll.0.options[i].entities)
                                    }
                                    attrOptions.append(TranslationMessageAttribute.Additional(text: translated.0, entities: translated.1))
                                }
                                
                                let solution: TranslationMessageAttribute.Additional?
                                if result.count > 1 + poll.0.options.count, !result[result.count - 1].0.isEmpty {
                                    solution = TranslationMessageAttribute.Additional(text: result[result.count - 1].0, entities: result[result.count - 1].1)
                                } else {
                                    solution = nil
                                }
                                
                                let title = result[0].0.isEmpty ? (poll.0.text, poll.0.textEntities) : result[0]
                                
                                let updatedAttribute: TranslationMessageAttribute = TranslationMessageAttribute(text: title.0, entities: title.1, additional: attrOptions, pollSolution: solution, toLang: toLang)
                                attributes.append(updatedAttribute)
                                
                                return .update(StoreMessage(id: currentMessage.id, customStableId: nil, globallyUniqueId: currentMessage.globallyUniqueId, groupingKey: currentMessage.groupingKey, threadId: currentMessage.threadId, timestamp: currentMessage.timestamp, flags: StoreMessageFlags(currentMessage.flags), tags: currentMessage.tags, globalTags: currentMessage.globalTags, localTags: currentMessage.localTags, forwardInfo: storeForwardInfo, authorId: currentMessage.author?.id, text: currentMessage.text, attributes: attributes, media: currentMessage.media))
                            })
                        }
                    }
                }
                
                if !audioTranscriptionsResults.isEmpty {
                    for (i, audioTranscription) in audioTranscriptions.enumerated() {
                        if let result = audioTranscriptionsResults[i] {
                            transaction.updateMessage(audioTranscription.1, update: { currentMessage in
                                let storeForwardInfo = currentMessage.forwardInfo.flatMap(StoreMessageForwardInfo.init)
                                var attributes = currentMessage.attributes.filter { !($0 is TranslationMessageAttribute) }
                                
                                let updatedAttribute: TranslationMessageAttribute = TranslationMessageAttribute(text: result.0, entities: result.1, additional: [], pollSolution: nil, toLang: toLang)
                                attributes.append(updatedAttribute)
                                
                                return .update(StoreMessage(id: currentMessage.id, customStableId: nil, globallyUniqueId: currentMessage.globallyUniqueId, groupingKey: currentMessage.groupingKey, threadId: currentMessage.threadId, timestamp: currentMessage.timestamp, flags: StoreMessageFlags(currentMessage.flags), tags: currentMessage.tags, globalTags: currentMessage.globalTags, localTags: currentMessage.localTags, forwardInfo: storeForwardInfo, authorId: currentMessage.author?.id, text: currentMessage.text, attributes: attributes, media: currentMessage.media))
                            })
                        }
                    }
                }
            }
            |> castError(TranslationError.self)
        }
    }
}

func _internal_togglePeerMessagesTranslationHidden
