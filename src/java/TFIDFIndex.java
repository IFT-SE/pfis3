import java.io.*;
import java.util.*;
import java.util.regex.*;


/**
 * This is an implementation of the Term Frequency - Inverse Document Frequency
 * algorithm for weighing the relevance of words across a set of plain-text
 * documents. Given a list of files, and a query this class will return the
 * relevance of the query relative to the files in the document base. Weight is
 * measured using a cosine similarity. The files parsed using this have all
 * syntax removed, camel-casing resolved and are stemmed prior to scoring.
 * 
 * @author cscaffid
 * 
 */
public class TFIDFIndex
{

    /**
     * maps from file identifier to tfidf vector (whose index is a word and
     * whose entries are actual tfidf values)
     */
    Map<String, Map<String, Float>> tfidfs = new HashMap<String, Map<String, Float>>();

    /**
     * maps from tokens to files that contain that word at all
     */
    Map<String, Set<String>> wordOccs = new HashMap<String, Set<String>>();

    /**
     * This constructor uses a root directory and file ending to determine which
     * files to index and include in the list of documents.
     * 
     * @param pathToSomeDirectoryOfFiles
     *            The full path to the root directory of files to index.
     * @param filenameEnding
     *            The filename ending of the files to index. If you want to
     *            index all files in the directory, use null.
     * @param recurse
     *            true if you want to use files in sub-directories, else false.
     * @throws Exception
     */
    public TFIDFIndex(String pathToSomeDirectoryOfFiles, String filenameEnding,
            boolean recurse) throws Exception
    {
        Queue<File> tovisit = new LinkedList<File>();
        tovisit.add(new File(pathToSomeDirectoryOfFiles));

        List<File> allTextFiles = new ArrayList<File>();
        while (tovisit.size() > 0)
        {

            File dir = tovisit.remove();
            File[] files = dir.listFiles();
            if (files == null) continue;
            for (File file : files)
            {
                if (file == null) continue;
                if (file.isDirectory())
                {
                    if (recurse) tovisit.add(file);
                }
                else
                {
                    if (filenameEnding == null
                            || file.getName().endsWith(filenameEnding))
                        allTextFiles.add(file);
                }
            }
        }
        init(allTextFiles);
    }

    /**
     * This construct simply takes a list of paths of the files to index. All
     * the listed files are included.
     * 
     * @param listOfFilesToIndex
     *            The list of file to index.
     * @throws Exception
     */
    public TFIDFIndex(List<String> listOfFilesToIndex) throws Exception
    {
        List<File> allTextFiles = new ArrayList<File>();
        for (String path : listOfFilesToIndex)
            allTextFiles.add(new File(path));
        init(allTextFiles);
    }

    /**
     * This constructor takes a map from the file path to the content of the
     * file.
     * 
     * @param mapFromFileIdToContent
     */
    public TFIDFIndex(Map<String, String> mapFromFileIdToContent)
    {
        init(mapFromFileIdToContent);
    }

    public static boolean DEBUG = false;

    /**
     * Returns the number of files that are included in this TF-TDF index.
     * 
     * @return The number of files that are included in this TF-TDF index.
     */
    public int numFiles()
    {
        return tfidfs.size();
    }

    /**
     * Creates a hash map of the file name to its content. Called by the
     * constructors of this object.
     * 
     * @param listOfFilesToIndex
     *            The list of files to index.
     * @throws Exception
     */
    private void init(List<File> listOfFilesToIndex) throws Exception
    {
        Map<String, String> content = new HashMap<String, String>();
        for (File file : listOfFilesToIndex)
            content.put(file.getCanonicalPath(), Util.getTextFrom(file));
        init(content);
    }

    /**
     * Performs the TF and the IDF calculations resolving camel casing, removing
     * syntax and stemming words. At the end of this method, all data structures
     * are ready to be used for the query phase.
     * 
     * @param identifierToContentMap
     *            Map from full path of file to file's contents.
     */
    private void init(Map<String, String> identifierToContentMap)
    {
        // compute term frequencies, then convert to tf, then go back and
        // convert to tfidf

        for (String fileIdentifier : identifierToContentMap.keySet())
        {
            if (DEBUG)
                System.err.println("now indexing: " + fileIdentifier);

            Map<String, Float> freq = new HashMap<String, Float>();
            List<String> tokens = getTokens(identifierToContentMap
                    .get(fileIdentifier));
            for (String token : tokens)
            {
                freq.put(token, freq.containsKey(token) ? freq.get(token) + 1
                        : 1); // count up how often each token appears in file

                Set<String> filesWithThatWord = null;
                if (wordOccs.containsKey(token))
                {
                    filesWithThatWord = wordOccs.get(token);
                }
                else
                {
                    filesWithThatWord = new HashSet<String>();
                    wordOccs.put(token, filesWithThatWord);
                }
                filesWithThatWord.add(fileIdentifier);
            }

            // now go back and convert term frequencies to tf part of tfidf
            float multiplier = 1F / tokens.size();
            Map<String, Float> tf = freq;
            for (String token : freq.keySet())
                tf.put(token, freq.get(token) * multiplier);

            tfidfs.put(fileIdentifier, tf);
        }

        // now that we know the total # docs for each word, go back and compute
        // the idf part of everything

        // string to idf value
        Map<String, Float> idfs = new HashMap<String, Float>();

        for (String token : wordOccs.keySet())
        {
            double idf = Math.log(identifierToContentMap.size()
                    / (double) wordOccs.get(token).size());
            idfs.put(token, (float) idf);
        }
        for (String fileIdentifier : identifierToContentMap.keySet())
        {
            Map<String, Float> tf = tfidfs.get(fileIdentifier);
            Map<String, Float> tfidf = tf;
            for (String token : tf.keySet())
                tfidf.put(token, tf.get(token) * idfs.get(token));
        }
        if (!DEBUG) System.err.println();
    }

    /**
     * This class wraps the results of the query into a tuple containing the
     * file's full path and it's TF-IDF score.
     * 
     * @author cscaffid
     * 
     */
    public static class QueryResult
    {
        /**
         * Contains full path to the file.
         */
        public String fileIdentifier;
        /**
         * Contains the resulting score from the TF-IDF query.
         */
        public Float goodnessOfMatch;
    }

    /**
     * Returns a sorted list of query results in descending order based on
     * scoring using the TF-IDF algorithm.
     * 
     * @param query
     *            The query text used to generate the scores.
     * @return A sorted list of type {@link QueryResult} in descending order.
     * @throws Exception
     */
    public List<QueryResult> query(String query) throws Exception
    {
        Set<String> filesToConsider = new HashSet<String>();
        Map<String, Float> qtokenTfidf = new HashMap<String, Float>();
        for (String qtoken : getTokens(query))
        {
            if (DEBUG) System.err.println("next query word: " + qtoken);
            if (!wordOccs.containsKey(qtoken)) continue; // nobody has this
                                                         // word... ignore it

            filesToConsider.addAll(wordOccs.get(qtoken));
            // This is an ugly and inefficient hack and needs to be fixed, but
            // it works:
            String fileWithWord = (String) (wordOccs.get(qtoken).toArray()[0]);

            float wordScore = tfidfs.get(fileWithWord).get(qtoken);
            if (!qtokenTfidf.containsKey(qtoken))
                qtokenTfidf.put(qtoken, wordScore);
        }

        Map<Float, Set<String>> tmprv = new TreeMap<Float, Set<String>>();

        // sort from highest to lowest value
        for (String fileIdentifier : filesToConsider)
        {
            Map<String, Float> tfidf = tfidfs.get(fileIdentifier);
            float cos = -cosine(qtokenTfidf, tfidf); // the - achieves reverse
                                                     // ordering of the sort

            if (tmprv.containsKey(cos))
                tmprv.get(cos).add(fileIdentifier);
            else
            {
                Set<String> tmp = new HashSet<String>();
                tmp.add(fileIdentifier);
                tmprv.put(cos, tmp);
            }
        }

        List<QueryResult> rv = new ArrayList<QueryResult>();
        for (float goodnessOfMatch : tmprv.keySet())
        {
            for (String fileIdentifier : tmprv.get(goodnessOfMatch))
            {
                QueryResult qr = new QueryResult();
                qr.fileIdentifier = fileIdentifier;
                qr.goodnessOfMatch = -goodnessOfMatch;
                rv.add(qr);
            }
        }
        return rv;
    }

    /**
     * Calculates the cosine similarity between two sets of words.
     * 
     * @param v1
     *            A map of words to tf-idf scores representing the query.
     * @param v2
     *            A map of words to tf-idf scores representing the document.
     * @return The cosine similarity score of that set
     */
    private static float cosine(Map<String, Float> v1, Map<String, Float> v2)
    {
        if (v1.size() > v2.size())
        {
            Map<String, Float> tmp = v1;
            v1 = v2;
            v2 = tmp;
        }

        float sum = 0;
        for (String idx : v1.keySet())
        {
            float val1 = v1.get(idx);
            float val2 = v2.containsKey(idx) ? v2.get(idx) : 0F;
            sum += val1 * val2;
        }

        float norm1sq = 0;
        for (String idx : v1.keySet())
        {
            float t = v1.get(idx);
            norm1sq += t * t;
        }

        float norm2sq = 0;
        for (String idx : v2.keySet())
        {
            float t = v2.get(idx);
            norm2sq += t * t;
        }

        return (float) (sum / (Math.sqrt(norm1sq) * Math.sqrt(norm2sq)));
    }

    /**
     * This method returns a list of camel-case resolved, stemmed and
     * syntax-free list of words from a source String. Returns only alpha
     * characters in the words.
     * 
     * @param source
     *            The String containing the text to tokenize.
     * @return A list of tokens from the source.
     */
    private static List<String> getTokens(String source)
    {
        StringBuffer temp = new StringBuffer();
        for (int i = 0; i < source.length(); i++)
        {
            char ch = source.charAt(i);
            if ((ch >= 'A' && ch <= 'Z') || (ch >= 'a' && ch <= 'z'))
                temp.append(ch);
            else
                temp.append(' ');
        }

        List<String> rv = new ArrayList<String>();
        for (String word : temp.toString().split(" "))
        {
            if (word.trim().length() == 0) continue;
            rv.addAll(humaniseCamelCase(word));
        }
        return rv;
    }

    /**
     * Resolves a camel-cased word into it's constituent parts. Ex: thisWayToGo
     * becomes [ this way to go ]
     * 
     * @param word
     *            The word to split.
     * @return The list of tokens after camel-case resolution.
     */
    public static List<String> humaniseCamelCase(String word)
    {
        Pattern pattern = Pattern.compile("([A-Z]|[a-z])[a-z]*");

        List<String> tokens = new ArrayList<String>();
        Matcher matcher = pattern.matcher(word);
        String acronym = "";
        while (matcher.find())
        {
            String found = matcher.group();
            if (found.matches("^[A-Z]$"))
            {
                acronym += found;
            }
            else
            {
                if (acronym.length() > 0)
                {
                    // we have an acronym to add before we continue
                    tokens.add(acronym.toLowerCase());
                    acronym = "";
                }
                tokens.add(stem(found.toLowerCase()));
            }
        }
        if (acronym.length() > 0)
        {
            tokens.add(stem(acronym.toLowerCase()));
        }

        return tokens;
    }

    /**
     * Calls the {@link Stemmer} and returns the stem of a word passed in. Ex:
     * becoming -> become or laughed -> laugh.
     * 
     * @param str
     *            The word to stem.
     * @return The stem of the word.
     */
    private static String stem(String str)
    {
        Stemmer stemmer = new Stemmer();
        for (int i = 0; i < str.length(); i++)
            stemmer.add(str.charAt(i));
        stemmer.stem();
        return stemmer.toString();
    }

}
