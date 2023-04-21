import java.nio.file.*;
import static java.nio.file.StandardWatchEventKinds.*;
import static java.nio.file.LinkOption.*;
import java.nio.file.attribute.*;
import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.*;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.LinkedList;
import java.util.Queue;

public class WatchDir {

    private final WatchService watcher;
    private final Map<WatchKey, Path> keys;
    private final boolean recursive;
    private boolean trace = false;

    @SuppressWarnings("unchecked")
    static <T> WatchEvent<T> cast(WatchEvent<?> event) {
        return (WatchEvent<T>) event;
    }

    /**
     * Register the given directory with the WatchService
     */
    private void register(Path dir) throws IOException {
        WatchKey key = dir.register(watcher, ENTRY_CREATE, ENTRY_DELETE, ENTRY_MODIFY);
        if (trace) {
            Path prev = keys.get(key);
            if (prev == null) {
                System.out.format("register: %s\n", dir);
            } else {
                if (!dir.equals(prev)) {
                    System.out.format("update: %s -> %s\n", prev, dir);
                }
            }
        }
        keys.put(key, dir);
    }

    /**
     * Register the given directory, and all its sub-directories, with the
     * WatchService.
     */
    private void registerAll(final Path start) throws IOException {
        // register directory and sub-directories
        Files.walkFileTree(start, new SimpleFileVisitor<Path>() {
            @Override
            public FileVisitResult preVisitDirectory(Path dir, BasicFileAttributes attrs)
                    throws IOException {
                register(dir);
                return FileVisitResult.CONTINUE;
            }
        });
    }

    /**
     * Creates a WatchService and registers the given directory
     */
    WatchDir(Path dir, boolean recursive) throws IOException {
        this.watcher = FileSystems.getDefault().newWatchService();
        this.keys = new HashMap<WatchKey, Path>();
        this.recursive = recursive;

        if (recursive) {
            System.out.format("Scanning %s ...\n", dir);
            registerAll(dir);
            System.out.println("Done.");
        } else {
            register(dir);
        }

        // enable trace after initial registration
        this.trace = true;
    }

    /**
     * Process all events for keys queued to the watcher
     */
    void processEvents() {
        for (;;) {

            // wait for key to be signalled
            WatchKey key;
            try {
                key = watcher.take();
            } catch (InterruptedException x) {
                return;
            }

            Path dir = keys.get(key);
            if (dir == null) {
                System.err.println("WatchKey not recognized!!");
                continue;
            }

            for (WatchEvent<?> event : key.pollEvents()) {
                WatchEvent.Kind kind = event.kind();

                // TBD - provide example of how OVERFLOW event is handled
                if (kind == OVERFLOW) {
                    continue;
                }

                // Context for directory entry event is the file name of entry
                WatchEvent<Path> ev = cast(event);
                Path name = ev.context();
                Path child = dir.resolve(name);

                // print out event
                System.out.format("%s: %s\n", event.kind().name(), child);

                if (event.kind() == ENTRY_CREATE) {
                    try {

                        int inserted_id = addFileToDB(child);
                        addVectorToDB(inserted_id);
                    } catch (Exception e) {
                        // TODO Auto-generated catch block
                        e.printStackTrace();
                    }
                } else if (event.kind() == ENTRY_DELETE) {
                    try {
                        deleteFileFromDB(child);

                    } catch (Exception e) {
                        // TODO: handle exception
                        e.printStackTrace();
                    }
                }

                // if directory is created, and watching recursively, then
                // register it and its sub-directories
                if (recursive && (kind == ENTRY_CREATE)) {
                    try {
                        if (Files.isDirectory(child, NOFOLLOW_LINKS)) {
                            registerAll(child);
                        }
                    } catch (IOException x) {
                        // ignore to keep sample readbale
                    }
                }
            }

            // reset key and remove from set if directory no longer accessible
            boolean valid = key.reset();
            if (!valid) {
                keys.remove(key);

                // all directories are inaccessible
                if (keys.isEmpty()) {
                    break;
                }
            }
        }
    }

    static void addVectorToDB(int myInteger) {
        try {
            URL url = new URL("http://localhost:6969/add_vector/" + myInteger);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("GET");
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setDoOutput(true);

            BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream()));
            StringBuilder response = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                response.append(line);
            }
            reader.close();

            System.out.println(response.toString());
            conn.disconnect();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    static void deleteVectorFromModel(int myInteger) {
        try {
            URL url = new URL("http://localhost:6969/delete/" + myInteger);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("GET");
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setDoOutput(true);

            BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream()));
            StringBuilder response = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                response.append(line);
            }
            reader.close();

            System.out.println(response.toString());
            conn.disconnect();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    static int addFileToDB(Path child) throws IOException, SQLException {

        BasicFileAttributes attr = Files.readAttributes(child, BasicFileAttributes.class);
        String fileType = Files.probeContentType(child);
        // System.out.println("type " + fileType);
        // System.out.println("filename " + child.getFileName());
        // System.out.println("creationTime: " + attr.creationTime());
        // System.out.println("lastAccessTime: " + attr.lastAccessTime());
        // System.out.println("lastModifiedTime: " + attr.lastModifiedTime());

        // System.out.println("isDirectory: " + attr.isDirectory());
        // System.out.println("isOther: " + attr.isOther());
        // System.out.println("isRegularFile: " + attr.isRegularFile());
        // System.out.println("isSymbolicLink: " + attr.isSymbolicLink());
        // System.out.println("size: " + attr.size());
        // System.out.println("fileKey: " + attr.fileKey());

        // System.out.println("--------------------------------------------------");
        connection = DriverManager.getConnection("jdbc:sqlite:sample.db");
        String sql = "INSERT INTO files (location, is_directory, type, created_at, filename, size) VALUES (?,?,?,?,?,?)";
        PreparedStatement stmt = connection.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS);
        stmt.setString(1, child.toString());
        stmt.setBoolean(2, attr.isDirectory());
        stmt.setString(3, fileType);
        stmt.setString(4, attr.creationTime().toString());
        stmt.setString(5, child.getFileName().toString());
        stmt.setLong(6, attr.size());

        stmt.executeUpdate();
        stmt.close();

        ResultSet generatedKeys = stmt.getGeneratedKeys();
        if (generatedKeys.next()) {
            int id = generatedKeys.getInt(1);
            return id;
        } else {
            throw new SQLException("Inserting row failed, no ID obtained.");
        }
    }

    static void deleteFileFromDB(Path path) throws SQLException {
        connection = DriverManager.getConnection("jdbc:sqlite:sample.db");
        Statement stmte = connection.createStatement();

        String selectSql = "SELECT id FROM files WHERE location=?";
        PreparedStatement selectStmt = connection.prepareStatement(selectSql);
        selectStmt.setString(1, path.toString());

        stmte.execute(
                "PRAGMA foreign_keys=ON");

        String deleteSql = "DELETE FROM files WHERE id=?";
        PreparedStatement deleteStmt = connection.prepareStatement(deleteSql);

        ResultSet rs = selectStmt.executeQuery();

        while (rs.next()) {
            int id = rs.getInt("id");

            // Set the parameter for the DELETE statement
            deleteStmt.setInt(1, id);

            // Execute the DELETE statement
            int numDeleted = deleteStmt.executeUpdate();

            if (numDeleted > 0) {
                deleteVectorFromModel(id);
            }
        }
    }

    static void usage() {
        System.err.println("usage: java WatchDir [-r] dir");
        System.exit(-1);
    }

    static Connection connection = null;

    static void scanDirectory(Path dir) {
        Queue<File> queue = new LinkedList<>();
        File root = new File(dir.toString());
        queue.add(root);

        while (!queue.isEmpty()) {
            File current = queue.poll();

            if (current.isDirectory()) {
                File[] files = current.listFiles();
                if (files != null) {
                    for (File file : files) {
                        queue.add(file);
                    }
                }
            } else {
                try {
                    addFileToDB(current.toPath());
                } catch (SQLException | IOException e) {
                    e.printStackTrace();
                }
            }
        }
    }

    public static void main(String[] args) throws IOException {
        // parse arguments
        // if (args.length == 0 || args.length > 2)
        // usage();

        try {
            Class.forName("org.sqlite.JDBC");
        } catch (ClassNotFoundException e1) {
            // TODO Auto-generated catch block
            e1.printStackTrace();
        }

        Connection connection = null;
        try {
            // create a database connection
            connection = DriverManager.getConnection("jdbc:sqlite:sample.db");
            Statement statement = connection.createStatement();
            statement.setQueryTimeout(30); // set timeout to 30 sec.
            statement.executeUpdate(
                    "DROP TABLE IF EXISTS files");
            statement.executeUpdate(
                    "DROP TABLE IF EXISTS embeddings");
            statement.executeUpdate(
                    "CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY AUTOINCREMENT, location STRING, is_directory INTEGER, type STRING, `created_at` TEXT, `filename` TEXT, `size` INTEGER )");
            statement.executeUpdate(
                    "CREATE TABLE IF NOT EXISTS embeddings (file_id INTEGER,vectors TEXT,FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE)");
        } catch (SQLException e) {
            // if the error message is "out of memory",
            // it probably means no database file is found
            System.err.println(e.getMessage());
        }

        // if (args.length == 0 || args.length > 2)
        // usage();

        boolean recursive = false;
        int dirArg = 0;
        // if (args[0].equals("-r")) {
        // if (args.length < 2)
        // usage();
        recursive = true;
        dirArg++;
        // }

        // register directory and process its events
        Path dir = Paths.get("C:\\Users\\sksou\\OneDrive\\Documents\\BEPRoject\\api_server\\FolderSync\\bin\\test");
        scanDirectory(dir);
        new WatchDir(dir, recursive).processEvents();
    }
}