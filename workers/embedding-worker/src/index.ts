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

// Payloads from the queue can be for a knowledge document or a chat message
interface DocumentPayload {
	document_id: string; // UUID
	text: string;
}

interface ChatMessagePayload {
	messageId: number; // BIGINT
	text: string;
}

type EmbeddingPayload = DocumentPayload | ChatMessagePayload;

// Type guard to differentiate payloads
function isDocumentPayload(payload: EmbeddingPayload): payload is DocumentPayload {
	return (payload as DocumentPayload).document_id !== undefined;
}

export default {
	async queue(batch: MessageBatch<EmbeddingPayload>, env: Env): Promise<void> {
		const supabase = createClient(env.SUPABASE_URL, env.SUPABASE_SERVICE_ROLE_KEY);

		for (const message of batch.messages) {
			const payload = message.body;
			let embedding: number[];

			try {
				// 1. Generate embedding for the text
				console.log(`Generating embedding for message: ${message.id}`);
				embedding = await generateEmbedding(payload.text, env);
			} catch (err: any) {
				console.error(`Failed to generate embedding for message ${message.id}: ${err.message}`);
				// Mark as failed in DB and ack to avoid retries for now
				if (isDocumentPayload(payload)) {
					await supabase.from('documents').update({ status: 'failed' }).eq('id', payload.document_id);
				} else {
					await supabase.from('messages').update({ status: 'failed' }).eq('id', payload.messageId);
				}
				message.ack();
				continue; // Move to the next message
			}

			try {
				if (isDocumentPayload(payload)) {
					// Logic for knowledge documents
					console.log(`Updating document ${payload.document_id} with embedding.`);
					const { error } = await supabase
						.from('documents')
						.update({
							embedding: embedding,
							status: 'completed',
						})
						.eq('id', payload.document_id);

					if (error) throw new Error(`Supabase document update error: ${error.message}`);
					console.log(`Successfully processed document ${payload.document_id}.`);

				} else {
					// Logic for chat messages
					console.log(`Storing embedding for message ${payload.messageId}.`);
					// A. Insert new document record for the message embedding
					const { error: insertError } = await supabase.from('documents').insert({
						message_id: payload.messageId,
						content: payload.text,
						embedding: embedding,
						status: 'completed', // Document record is immediately complete
					});
					if (insertError) throw new Error(`Supabase insert error: ${insertError.message}`);

					// B. Update original message status
					const { error: updateError } = await supabase
						.from('messages')
						.update({ status: 'completed' })
						.eq('id', payload.messageId);
					if (updateError) {
						// This is not a fatal error for the embedding, but should be logged.
						console.warn(`Failed to update message status for ${payload.messageId}: ${updateError.message}`);
					}
					console.log(`Successfully processed message ${payload.messageId}.`);
				}

				message.ack(); // Mark as processed successfully
			} catch (err: any) {
				console.error(`Error saving embedding for message ID ${message.id}: ${err.message}`);
				// A DB error occurred, retry the message.
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
