import java.util.*;
import java.net.*;
import java.io.*;

/**
 * The <code>Util</code> class contains additional helpful utilities outside the
 * context of IFT. Specifically, this class contains methods for reading files,
 * urls and delimited strings.
 * 
 * @author cscaffid
 * 
 */
public class Util
{
    /**
     * Resolves a url into its representative html file. That html file is then
     * returned as a String.
     * 
     * @param url
     *            The url to gather html from. Ex: http://google.com
     * @param useCache
     *            True if you want to use a local file to store content prior to
     *            returning a String.
     * @return Returns the String representation of the url's html.
     * @throws Exception
     */
    public static String getTextFrom(URL url, boolean useCache)
            throws Exception
    {
        StringBuffer keyMaker = new StringBuffer();
        String ux = url.toString().toLowerCase();
        for (int c = 0; c < ux.length(); c++)
        {
            char ch = ux.charAt(c);
            if ((ch >= 'a' && ch <= 'z') || (ch >= '0' && ch <= '9'))
                keyMaker.append(ch);
            if (ux.length() > 100) break;
        }
        File cacheDir = new File("cache" + File.separatorChar + url.hashCode());
        File cacheFile = new File(cacheDir.toString() + File.separatorChar
                + keyMaker + ".txt");
        if (useCache)
        {
            if (!cacheDir.exists()) cacheDir.mkdirs();
            if (cacheFile.exists()) return getTextFrom(cacheFile);
        }

        try
        {
            URLConnection conn = url.openConnection();
            Reader reader = new InputStreamReader(conn.getInputStream());

            StringBuffer rv = new StringBuffer();
            char[] buffer = new char[512];
            int nread = 0;
            while ((nread = reader.read(buffer, 0, buffer.length)) > 0)
            {
                rv.append(buffer, 0, nread);
            }
            reader.close();

            String srv = rv.toString();

            if (useCache)
            {
                FileWriter wr = new FileWriter(cacheFile);
                wr.write(srv);
                wr.flush();
                wr.close();
            }
            return srv;
        }
        catch (java.net.UnknownHostException ex)
        {
            return "";
        }

    }

    /**
     * Returns the content of a file as a String.
     * 
     * @param file
     *            The path to the file.
     * @return The String containing the contents of that file.
     * @throws Exception
     */
    public static String getTextFrom(File file) throws Exception
    {
        long len = file.length();
        char[] buffer = new char[(int) len];
        FileReader reader = new FileReader(file);
        reader.read(buffer, 0, buffer.length);
        reader.close();
        return new String(buffer);
    }

    /**
     * Returns a list of Strings based on start and end delimiters from an input
     * String.
     * 
     * @param text
     *            The input String to tokenize.
     * @param startMarker
     *            The starting String signifying the beginning of a token.
     * @param endMarker
     *            The ending String signifying the end of a token.
     * @return
     */
    public static List<String> grabDelimitedValues(String text,
            String startMarker, String endMarker)
    {
        return grabDelimitedValues0(text, startMarker, endMarker, false);
    }

    /**
     * Returns a single token from an input String based on start and end
     * delimiters.
     * 
     * @param text
     *            The input String to tokenize.
     * @param startMarker
     *            The starting String signifying the beginning of a token.
     * @param endMarker
     *            The ending String signifying the end of a token.
     * @return
     */
    public static String grabDelimitedValue(String text, String startMarker,
            String endMarker)
    {
        List<String> tmp = grabDelimitedValues0(text, startMarker, endMarker,
                true);
        return tmp.size() > 0 ? tmp.get(0) : null;
    }

    /**
     * Helper method to get the delimited tokens according to a start and end
     * delimiter from an input string. This helper has a flag to see if the List
     * contains only the first token, or all tokens.
     * 
     * @param text
     *            The input String to be tokenized.
     * @param startMarker
     *            The starting String signifying the beginning of a token.
     * @param endMarker
     *            The ending String signifying the end of a token.
     * @param stopAtOne
     *            false to get all tokens, true to get only first token.
     * @return
     */
    private static List<String> grabDelimitedValues0(String text,
            String startMarker, String endMarker, boolean stopAtOne)
    {
        List<String> rv = new ArrayList<String>();

        int sloc = 0;
        while (true)
        {
            sloc = text.indexOf(startMarker, sloc);
            if (sloc == -1) break;
            sloc += startMarker.length();
            int eloc = text.indexOf(endMarker, sloc);
            if (eloc == -1) break;
            rv.add(text.substring(sloc, eloc));
            if (stopAtOne) break;
        }

        return rv;
    }

    /**
     * Cleans the HTML by replacing the characters that exist in the ascii table
     * prior to the character ' ' with a ' ' (space).
     * 
     * @param html
     *            The String of the html to clean.
     * @return The cleaned up String representation of the html.
     */
    public static String clean(String html)
    {
        if (html == null) return null;
        StringBuffer rv = new StringBuffer();
        boolean intag = false;
        for (int i = 0; i < html.length(); i++)
        {
            char ch = html.charAt(i);
            if (ch == '<')
            {
                intag = true;
            }
            else if (ch == '>')
            {
                intag = false;
            }
            else if (intag == false)
            {
                rv.append(ch < ' ' ? ' ' : ch);
            }
        }
        return rv.toString();
    }
}
