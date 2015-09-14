import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.channels.FileChannel;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.List;
import java.util.Scanner;

public class BuildNaiveModelFiles
{
	private static Connection conn;
	private static Statement stat;
	private static List<NavigateTo> navigations;

	public static class NavigateTo
	{
		long _msOffset;
		String _fileName, _user, _agent;
		int _textOffset;

		public NavigateTo(long msOffset, String fileName, int tOffset,
		        String user, String agent)
		{
			_msOffset = msOffset;
			_fileName = fileName;
			_textOffset = tOffset;
			_user = user;
			_agent = agent;
		}
	}

	public static void main(String args[])
	{
		// initDbConnection("db/ParticipantK-2010-01-25-sqlite-Accurate.db");
		// seeMethodDeclarationOffsets();
		// closeDbConnection();

		//copyFile("data/ParticipantK-2010-01-25-sqlite-Accurate.db",
		//        "data/ParticipantK-2010-01-25-sqlite-Accurate_copy.db");
		//loadScrollingEvents("data/ScrollingAccurate.txt");
		//initDbConnection("data/ParticipantK-2010-01-25-sqlite-Accurate_copy.db");
		//deleteTextSelectionEvents();
		//addScrollingEvents();
		//closeDbConnection();
		createDbCopies("data/ParticipantK_newNavs.db", args[0]);
	}

	public static void copyFile(File in, File out) throws IOException
	{
		FileChannel inChannel = new FileInputStream(in).getChannel();
		FileChannel outChannel = new FileOutputStream(out).getChannel();
		try
		{
			inChannel.transferTo(0, inChannel.size(), outChannel);
		}
		catch (IOException e)
		{
			throw e;
		}
		finally
		{
			if (inChannel != null) inChannel.close();
			if (outChannel != null) outChannel.close();
		}
	}

	private static void copyFile(String originalFilePath, String newFilePath)
	{
		try
		{
			copyFile(new File(originalFilePath), new File(newFilePath));
		}
		catch (IOException e)
		{
			e.printStackTrace();
		}
	}

	private static void loadScrollingEvents(String pathToFile)
	{
		System.out.println("Reading in navigation text file...");

		try
		{
			navigations = new ArrayList<NavigateTo>();
			Scanner sc = new Scanner(new File(pathToFile));
			String line = null;
			String[] tokens = null;

			while (sc.hasNext())
			{
				line = sc.nextLine();
				tokens = line.split("\t");
				// if (tokens.length == 7)
				// {
				// navigations.add(new NavigateTo(Long.parseLong(tokens[1]),
				// tokens[4], Integer.parseInt(tokens[6])));
				// }
				if (tokens.length == 5)
				{
					navigations.add(new NavigateTo(Long.parseLong(tokens[2]),
					        tokens[0], Integer.parseInt(tokens[1]), tokens[3],
					        tokens[4]));
				}
			}
			sc.close();

		}
		catch (FileNotFoundException e)
		{
			e.printStackTrace();
		}

	}

	private static void initDbConnection(String dbPath)
	{
		System.out.println("Initializing connection...");
		try
		{
			Class.forName("org.sqlite.JDBC");
			conn = DriverManager.getConnection("jdbc:sqlite:" + dbPath);
			stat = conn.createStatement();
		}
		catch (SQLException e)
		{
			e.printStackTrace();
		}
		catch (ClassNotFoundException e)
		{
			e.printStackTrace();
		}
	}

	private static void deleteTextSelectionEvents()
	{
		System.out.println("Delete text selection events...");

		try
		{
			String query = "delete from logger_log "
			        + "where action in ('Text selection', 'Text selection offset');";
			stat = conn.createStatement();

			stat.executeUpdate(query);
			stat.close();
		}
		catch (SQLException e)
		{
			// TODO Auto-generated catch block
			e.printStackTrace();
		}

	}

	private static void addScrollingEvents()
	{
		// 'c4f2437e-6d7b-4392-b68c-0fa7348facbd'
		// 'a23fe51d-196a-45b3-addf-3db4e8423e4f'
		System.out.println("Adding new events...");
		int i = 100000;
		java.sql.Date date;

		try
		{
			PreparedStatement pstat = conn
			        .prepareStatement("insert into logger_log "
			                + "(id, user, timestamp, action, target, referrer, agent) "
			                + "values (?, ?, datetime(?), ?, ?, ?, ?);");

			SimpleDateFormat sdf = new SimpleDateFormat(
			        "yyyy-MM-dd HH:mm:ss.SSS000000");

			for (NavigateTo action : navigations)
			{

				date = new java.sql.Date(action._msOffset);

				pstat.setInt(1, i++);
				pstat.setString(2, action._user);
				pstat.setString(3, sdf.format(date));
				pstat.setString(4, "Text selection offset");
				pstat.setString(5, action._fileName);
				pstat.setString(6, "" + action._textOffset);
				pstat.setString(7, action._agent);

				pstat.executeUpdate();
				// System.out.println(sdf.format(date));
			}
			pstat.close();

		}
		catch (SQLException e)
		{
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

	private static void closeDbConnection()
	{
		try
		{
			if (conn != null && !conn.isClosed()) conn.close();
		}
		catch (SQLException e)
		{
			e.printStackTrace();
		}
	}

	private static void createDbCopies(String dbPath, String outputDir)
	{
		System.out.println("Creating db copies...");
		List<String> dates = new ArrayList<String>();

		try
		{
			initDbConnection(dbPath);
			String query = "select timestamp from logger_log where action = 'Text selection offset' order by timestamp;";
			ResultSet rs = stat.executeQuery(query);
			PreparedStatement pstat = null;

			while (rs.next())
			{
				dates.add(rs.getString("timestamp"));
			}
			rs.close();
			stat.close();
			closeDbConnection();

			int i = 1;
			String newDbDir, newDbPath;

			for (String d : dates)
			{
				newDbDir = outputDir + "/nav_" + i++ + "/";
				newDbPath = newDbDir + "ParticipantK-2010-01-25-sqlite.db";

				System.out.println("\tCreating " + newDbPath);

				new File(newDbDir).mkdirs();
				copyFile(dbPath, newDbPath);
				System.out.println("Connecting to " + newDbPath + "...");
				initDbConnection(newDbPath);
				pstat = conn
				        .prepareStatement("delete from logger_log where timestamp > ?;");
				pstat.setString(1, d);
				System.out.println(pstat.executeUpdate() + " rows deleted");
				pstat.close();
				closeDbConnection();
				System.out.println("Closing " + newDbPath + "...");
			}
			System.out.println("Done");
		}
		catch (SQLException e)
		{
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
}