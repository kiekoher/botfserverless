import { createClient } from '@supabase/supabase-js';
import 'dotenv/config';

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_KEY;

if (!supabaseUrl || !supabaseKey) {
    console.error("Error: Las variables de entorno SUPABASE_URL y SUPABASE_KEY son obligatorias.");
    process.exit(1);
}

export const supabase = createClient(supabaseUrl, supabaseKey);

export const logConversation = async (userId, userMessage, botResponse, contextChunks = []) => {
    try {
        const { error } = await supabase.from('conversations').insert({
            user_id: userId, user_message: userMessage, bot_response: botResponse, context_chunks: contextChunks
        });
        if (error) throw error;
    } catch (error) {
        console.error('Error al registrar la conversación:', error.message);
    }
};

export const insertDocument = async (fileName, content) => {
    try {
        const { data, error } = await supabase.from('documents').insert({ file_name: fileName, content }).select('id').single();
        if (error) throw error;
        return data.id;
    } catch (error) {
        console.error('Error al insertar documento:', error.message); return null;
    }
};

export const insertChunks = async (chunks) => {
    if (!chunks || chunks.length === 0) return true;
    try {
        const { error } = await supabase.from('chunks').insert(chunks);
        if (error) throw error;
        return true;
    } catch (error) {
        console.error('Error al insertar chunks:', error.message); return false;
    }
};
