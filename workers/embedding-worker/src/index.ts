import { createClient } from '@supabase/supabase-js';
import { GoogleAuth } from 'google-auth-library';

// Define the structure of the environment variables
export interface Env {
	SUPABASE_URL: string;
	SUPABASE_SERVICE_ROLE_KEY: string;
	GOOGLE_API_PROJECT_ID: string;
	GOOGLE_API_LOCATION: string;
	// The GOOGLE_APPLICATION_CREDENTIALS_JSON secret is also implicitly available
}

// The structure of the message body coming from the transcription worker
interface EmbeddingPayload {
	messageId: number;
	text: string;
}

export default {
	async queue(batch: MessageBatch<EmbeddingPayload>, env: Env): Promise<void> {
		const supabase = createClient(env.SUPABASE_URL, env.SUPABASE_SERVICE_ROLE_KEY);

		for (const message of batch.messages) {
			try {
				const payload = message.body;
				console.log(`Generating embedding for message: ${payload.messageId}`);

				// 1. Generate embedding for the text
				const embedding = await generateEmbedding(payload.text, env);

				// 2. Store the embedding in Supabase (e.g., in a 'documents' table)
				// This assumes a table `documents` with a foreign key to `messages`
				// and a vector column named `embedding`.
				const { error: insertError } = await supabase.from('documents').insert({
					message_id: payload.messageId,
					content: payload.text,
					embedding: embedding,
				});

				if (insertError) {
					throw new Error(`Supabase insert error: ${insertError.message}`);
				}

				// 3. Update the original message status to 'completed'
				const { error: updateError } = await supabase
					.from('messages')
					.update({ status: 'completed' })
					.eq('id', payload.messageId);

				if (updateError) {
					// This is not ideal, as the embedding is already stored, but we log it.
					console.error(`Failed to update message status for ${payload.messageId}: ${updateError.message}`);
				}

				console.log(`Successfully processed and stored embedding for message ${payload.messageId}.`);
				message.ack();

			} catch (err: any) {
				console.error(`Error processing embedding for message ID ${message.id}: ${err.message}`);
				message.retry();
			}
		}
	},
};

async function generateEmbedding(text: string, env: Env): Promise<number[]> {
	// Using Google Auth Library to get credentials and make a request to the Vertex AI Embedding API
	const auth = new GoogleAuth({
		scopes: 'https://www.googleapis.com/auth/cloud-platform',
	});
	const client = await auth.getClient();
	const accessToken = (await client.getAccessToken()).token;

	const model = 'text-embedding-004'; // Example model
	const url = `https://${env.GOOGLE_API_LOCATION}-aiplatform.googleapis.com/v1/projects/${env.GOOGLE_API_PROJECT_ID}/locations/${env.GOOGLE_API_LOCATION}/publishers/google/models/${model}:predict`;

	const response = await fetch(url, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${accessToken}`,
			'Content-Type': 'application/json',
		},
		body: JSON.stringify({
			instances: [{ content: text }],
		}),
	});

	if (!response.ok) {
		const errorBody = await response.text();
		throw new Error(`Failed to generate embedding: ${response.status} ${errorBody}`);
	}

	const data = await response.json();
	const embedding = data?.predictions[0]?.embeddings?.values;

	if (!embedding) {
		throw new Error('Invalid response from embedding API');
	}

	return embedding;
}
