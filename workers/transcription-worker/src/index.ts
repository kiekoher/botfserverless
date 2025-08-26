import { createClient } from '@supabase/supabase-js';
import { S3Client, GetObjectCommand } from '@aws-sdk/client-s3';
import { SpeechClient } from '@google-cloud/speech';

// Define the structure of the environment variables (secrets and vars)
export interface Env {
	SUPABASE_URL: string;
	SUPABASE_SERVICE_ROLE_KEY: string;
	R2_BUCKET_NAME: string;
	R2_ACCOUNT_ID: string;
	R2_ACCESS_KEY_ID: string;
	R2_SECRET_ACCESS_KEY: string;
	GOOGLE_APPLICATION_CREDENTIALS_JSON: string;
	// Binding to the queue for the next step in the pipeline
	EMBEDDING_QUEUE: Queue;
}

// The structure of the message body coming from the API
interface MessagePayload {
	userId: string;
	userName: string;
	chatId: string;
	timestamp: string;
	mediaKey: string;
	mediaType: string;
}

export default {
	async queue(batch: MessageBatch<MessagePayload>, env: Env): Promise<void> {
		const supabase = createClient(env.SUPABASE_URL, env.SUPABASE_SERVICE_ROLE_KEY);

		for (const message of batch.messages) {
			try {
				const payload = message.body;
				console.log(`Processing message for user: ${payload.userId}`);

				// 1. Create initial record in Supabase
				const { data: messageRecord, error: createError } = await supabase
					.from('messages')
					.insert({
						user_id: payload.userId,
						conversation_id: payload.chatId,
						content: '[AUDIO]',
						status: 'transcribing',
						metadata: {
							mediaKey: payload.mediaKey,
							mediaType: payload.mediaType,
							userName: payload.userName,
						},
					})
					.select()
					.single();

				if (createError) throw new Error(`Supabase create error: ${createError.message}`);

				// 2. Download audio from R2
				const audioBuffer = await downloadFromR2(payload.mediaKey, env);

				// 3. Transcribe with Google Speech-to-Text
				const transcript = await transcribeAudio(audioBuffer, env);
				console.log(`Transcription result: "${transcript}"`);

				// 4. Update the record in Supabase with the transcript
				const { error: updateError } = await supabase
					.from('messages')
					.update({ content: transcript, status: 'processing_embedding' })
					.eq('id', messageRecord.id);

				if (updateError) throw new Error(`Supabase update error: ${updateError.message}`);

				// 5. Enqueue for the next worker (embedding)
				const embeddingPayload = {
					messageId: messageRecord.id,
					text: transcript,
				};
				await env.EMBEDDING_QUEUE.send(embeddingPayload);
				console.log(`Enqueued message ${messageRecord.id} for embedding worker.`);

				message.ack();

			} catch (err: any) {
				console.error(`Error processing message ID ${message.id}: ${err.message}`);
				// Retry the message on failure
				message.retry();
			}
		}
	},
};


async function downloadFromR2(key: string, env: Env): Promise<Buffer> {
	const s3Client = new S3Client({
		region: 'auto',
		endpoint: `https://${env.R2_ACCOUNT_ID}.r2.cloudflarestorage.com`,
		credentials: {
			accessKeyId: env.R2_ACCESS_KEY_ID,
			secretAccessKey: env.R2_SECRET_ACCESS_KEY,
		},
	});

	console.log(`Downloading from R2: ${key}`);
	const command = new GetObjectCommand({
		Bucket: env.R2_BUCKET_NAME,
		Key: key,
	});

	const response = await s3Client.send(command);
	const byteArray = await response.Body?.transformToByteArray();
	if (!byteArray) {
		throw new Error('Failed to download file from R2: Body is empty.');
	}
	return Buffer.from(byteArray);
}

async function transcribeAudio(audioBuffer: Buffer, env: Env): Promise<string> {
	const credentials = JSON.parse(env.GOOGLE_APPLICATION_CREDENTIALS_JSON);
	const speechClient = new SpeechClient({ credentials });

	const audio = {
		content: audioBuffer.toString('base64'),
	};
	const config = {
		encoding: 'OGG_OPUS' as const, // Assuming ogg/opus from WhatsApp
		sampleRateHertz: 16000,
		languageCode: 'es-US', // Example language code
	};
	const request = {
		audio: audio,
		config: config,
	};

	console.log('Sending audio to Google Speech-to-Text API...');
	const [response] = await speechClient.recognize(request);
	const transcription = response.results
		?.map((result) => result.alternatives?.[0].transcript)
		.join('\n');

	if (!transcription) {
		throw new Error('Google Speech-to-Text API returned no transcription.');
	}

	return transcription;
}
